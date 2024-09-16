from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, FileResponse, Http404, JsonResponse, HttpResponseRedirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from .forms import UploadFileForm, GPTForm
from .models import CalculationResult
from .models import GptResult
from io import BytesIO
import os
import datetime
import zipfile
import pandas as pd
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .utils.calculation import (
    calculate_fees_issued_date, calculate_fees_filing_date, post_process_fees, date_check
)
from .utils.excel_utils import read_patent_data, extract_patent_info
from .utils.fees_reader import read_fees_data
from .utils.total import add_total_fees_per_patent, calculate_grand_total
from .utils.overview import create_overview_sheet, format_dates_and_currency
from .utils.locate import locate_country_code_in_fees
from .utils.gpt_utils.operations import clean_and_extract_relevant_columns, categorize_claims, save_to_excel, handle_multiple_requests
from .utils.exceptions import MissingRequiredColumnsError, InvalidCountryCodeError, ExcelFileReadError, ExcelError
from .utils.gpt_utils.exceptions import GPTInvalidColumnsError

###################################### LOGIN/LOGOUT #########################################

# Login view
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # Redirect to home after login
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'registration/login.html')

# Logout view
def logout_view(request):
    logout(request)
    return redirect('login')  # Redirect to login page after logout


############################################ HOME ############################################
def home(request):
    return render(request, 'calculator/home.html', context={'user' : request.user})

############################################ FEES VIEW ############################################

def view_fees_dollars(request):
    file_path = os.path.join(settings.BASE_DIR, 'calculator', 'data', 'feesdollars.xlsx')
    df = pd.read_excel(file_path)
    data = df.to_html(classes='table table-striped', index=False)
    return render(request, 'calculator/feesdollars.html', {'data': data})

def download_fees(request):
    file_path = os.path.join(settings.BASE_DIR, 'calculator', 'data', 'feesdollars.xlsx')
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='FeesDollars.xlsx')

def upload_fees(request):
    if request.method == 'POST' and request.FILES.get('fees_file'):
        file = request.FILES['fees_file']
        file_path = os.path.join(settings.BASE_DIR, 'calculator', 'data', 'feesdollars.xlsx')
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    return JsonResponse({'error': 'Invalid request'}, status=400)

############################################ CALCULATION VIEW ############################################
@login_required  # Ensure the user is logged in before accessing this view
def locate_country_codes_and_names(request):
    fees_info_path = os.path.join(settings.BASE_DIR, 'calculator', 'data', 'feesdollars.xlsx')
    fees_info = read_fees_data(fees_info_path)
    country_codes_and_names = {}

    for column in fees_info.columns:
        if fees_info.iloc[0][column].strip() in ['Publication Date', 'File Date']:  # Filter out other types if necessary
            country_codes_and_names[column] = {
                'country': fees_info.iloc[1][column],
                'type': fees_info.iloc[0][column]
            }

    return country_codes_and_names

def calculate_fees_view(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data["file"]

            try:
                # Read patent data and validate columns
                full_patent_df, patent_df = read_patent_data(file)

                # Extract patent info
                patent_info = extract_patent_info(patent_df)
                
                # Read fees data
                fees_info_path = os.path.join(settings.BASE_DIR, 'calculator', 'data', 'feesdollars.xlsx')
                fees_info = read_fees_data(fees_info_path)

                # Locate country code in fees and calculate fees
                date_types = locate_country_code_in_fees(patent_info, fees_info)

                # Proceed with the rest of the logic...
                project_id = CalculationResult.objects.count() + 1
                original_filename = os.path.splitext(file.name)[0]
                new_filename = f"TIPA_MC_{project_id}_{original_filename}.xlsx"
                
                fs = FileSystemStorage()
                filename = fs.save(new_filename, file)
                file_path = fs.path(filename)

                full_patent_df, patent_df = read_patent_data(file_path)
                patent_info = extract_patent_info(patent_df)

                output_filename = f"TIPA_MC_{project_id}_{original_filename}.xlsx"
                output_file_path = os.path.join(settings.BASE_DIR, 'database', 'calculator', output_filename)

                results_df = patent_df.copy()
                results_df['Date Type'] = None

                for i, patent in enumerate(patent_info):
                    results_df = date_check(patent, date_types, fees_info, results_df, i)

                results_df = post_process_fees(results_df)
                results_df = add_total_fees_per_patent(results_df)
                results_df = calculate_grand_total(results_df)
                #results_df = results_df.drop(columns=['Date Type'])

                results_df.to_excel(output_file_path, index=False)
                create_overview_sheet(output_file_path)
                format_dates_and_currency(output_file_path)

                CalculationResult.objects.create(
                    filename=output_filename,
                    file_path=output_file_path,
                    created_by=request.user
                )

                return redirect('calculate_fees')

            # Handle missing columns specifically
            except MissingRequiredColumnsError as e:
                return render_error_page(request, form, str(e))

            # Handle any Excel-related errors
            except ExcelError as e:
                return render_error_page(request, form, str(e))

            # Handle any other unexpected errors
            except Exception as e:
                return render_error_page(request, form, "An unexpected error occurred. Please try again later.")

    else:
        form = UploadFileForm()

    result_files_calculation = CalculationResult.objects.filter(file_path__startswith=os.path.join(settings.BASE_DIR, 'database', 'calculator')).order_by('-created_at')

    country_codes_and_names = locate_country_codes_and_names(request)

    context = {
        'form': form,
        'result_files_calculation': result_files_calculation,
        'country_codes_and_names': country_codes_and_names
    }

    return render(request, 'calculator/calculate.html', context)

def render_error_page(request, form, error_message):
    result_files_calculation = CalculationResult.objects.filter(
        file_path__startswith=os.path.join(settings.BASE_DIR, 'database', 'calculator')
    ).order_by('-created_at')

    # Ensure country_codes_and_names is passed when rendering the error
    country_codes_and_names = locate_country_codes_and_names(request)

    return render(request, 'calculator/calculate.html', {
        'form': form,
        'error_message': error_message,
        'result_files_calculation': result_files_calculation,
        'country_codes_and_names': country_codes_and_names  # Add this line to ensure it's passed
    })

#result_files_calculation = CalculationResult.objects.filter(file_path__startswith=os.path.join(settings.BASE_DIR, 'database', 'calculator')).order_by('-created_at')
def handle_uploaded_file(f):
    df = pd.read_excel(f)
    df['Total'] = df.sum(axis=1)
    return df


############################################ FILE DOWNLOAD ############################################
def bulk_download(request):
    if request.method == "POST":
        selected_files = request.POST.getlist('selected_files')

        if not selected_files:
            return Http404("No files selected for download.")

        if len(selected_files) == 1:
            # If only one file is selected, return it directly
            filename = selected_files[0]
            
            # Determine which model to use based on the prefix
            if filename.startswith('TIPA_MC_'):
                Model = CalculationResult
            else:
                Model = GptResult
            
            result_file = get_object_or_404(Model, filename=filename)
            file_path = result_file.file_path

            if os.path.exists(file_path):
                return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=result_file.filename)
            else:
                raise Http404("File not found")

        else:
            # If multiple files are selected, create a ZIP archive
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                for filename in selected_files:
                    # Determine which model to use based on the prefix
                    if filename.startswith('TIPA_MC_'):
                        Model = CalculationResult
                    else:
                        Model = GptResult

                    result_file = get_object_or_404(Model, filename=filename)
                    file_path = result_file.file_path
                    if os.path.exists(file_path):
                        zip_file.write(file_path, arcname=os.path.basename(file_path))

            zip_buffer.seek(0)
            response = HttpResponse(zip_buffer, content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename=selected_files.zip'
            return response

    raise Http404("Invalid request method.")


############################################  GPT VIEWS ############################################
@login_required
def gpt_categorize_view(request):
    if request.method == 'POST':
        form = GPTForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            prompt = form.cleaned_data['prompt']
            model = form.cleaned_data['model']
            prefix = request.POST.get('prefix', 'TIPA')  # Default to TIPA if not selected

            # Get the user-selected columns
            selected_columns = request.POST.getlist('columns')

            try:
                # Save the uploaded file
                fs = FileSystemStorage()
                filename = fs.save(file.name, file)
                file_path = fs.path(filename)

                # Process the Excel file (extract selected columns)
                df = clean_and_extract_relevant_columns(file_path, selected_columns)

                # Categorize claims using the GPT model
                categorized_df = categorize_claims(df, model, prompt, selected_columns)

                # Ensure the output directory exists
                output_dir = os.path.join(settings.BASE_DIR, 'database', 'GPT', 'Categorization')
                os.makedirs(output_dir, exist_ok=True)

                # Generate the new filename with the selected prefix and project ID
                project_id = GptResult.objects.count() + 1
                output_filename = f"{prefix}_{project_id:04d}_{filename}"
                output_file_path = os.path.join(output_dir, output_filename)

                # Save the results to Excel
                save_to_excel(categorized_df, output_file_path)

                # Store the result in the database
                GptResult.objects.create(
                    filename=output_filename,
                    file_path=output_file_path,
                    prompt=prompt,
                    model_used=model,
                    created_by=request.user
                )

                return redirect('gpt-categorize')

            except GPTInvalidColumnsError as e:
                result_files_gpt = GptResult.objects.filter(file_path__startswith=os.path.join(settings.BASE_DIR, 'database', 'GPT', 'Categorization')).order_by('-created_at')
                return render(request, 'calculator/gpt.html', {
                    'form': form,
                    'error_message': str(e),  # Display the custom exception message
                    'result_files_gpt': result_files_gpt
                })

            except Exception as e:
                result_files_gpt = GptResult.objects.filter(file_path__startswith=os.path.join(settings.BASE_DIR, 'database', 'GPT', 'Categorization')).order_by('-created_at')
                return render(request, 'calculator/gpt.html', {
                    'form': form,
                    'error_message': f"Failed to process the Excel file: {str(e)}",
                    'result_files_gpt': result_files_gpt
                })

    else:
        form = GPTForm()

    result_files_gpt = GptResult.objects.filter(file_path__startswith=os.path.join(settings.BASE_DIR, 'database', 'GPT', 'Categorization')).order_by('-created_at')

    context = {
        'form': form,
        'result_files_gpt': result_files_gpt,
    }
    
    return render(request, 'calculator/gpt.html', context)


#result_files_gpt = GptResult.objects.filter(file_path__startswith=os.path.join(settings.BASE_DIR, 'database', 'GPT', 'Categorization')).order_by('-created_at')

