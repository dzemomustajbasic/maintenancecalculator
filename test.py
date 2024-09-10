import os
import pandas as pd


results_dir = os.path.join(os.getcwd(), 'calculator', 'results')
if not os.path.exists(results_dir):
    os.makedirs(results_dir)


print(f"Results directory path: {results_dir}")
print(f"Results directory exists: {os.path.exists(results_dir)}")

df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})


output_file_path = os.path.join(results_dir, 'test_output.xlsx')


df.to_excel(output_file_path, index=False)

print(f"fajlas sejvan tu {output_file_path}")
print(f"postoji {os.path.exists(output_file_path)}")