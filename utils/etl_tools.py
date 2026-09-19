import os
import pandas as pd
import requests


class ETLTools:
    
    def __init__(self) -> None:
        pass
    
    def extract_load(self, url :str, output_folder :str, format:str):
        """This Tool extrcts the data from the api (url) & loads it  into the desired location (output_folder)

        Args:
            url (str): The API endpoint from which the data needs to be extracted
            output_folder (str) : The folder where the extracted data needs to be stored
            format (str) : The format of the data
        Returns:
            str: path to the project root
        """
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
        output_folder=  os.path.join(project_root, output_folder)
        try: 
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            filename = os.path.join(output_folder, f"Extracted_data.{format}")
            os.makedirs(output_folder, exist_ok=True)
            # write the data
            df  = pd.json_normalize(data["results"])
            if format=="csv":
                df.to_csv(filename,index=False)
            elif format=="json":
                df.to_json(filename, orient="records", lines=True)
            elif format=="parquet":
                df.to_parquet(filename, index=False)
            else:
                return f"Unsupported format: {format}"
            return f" Data successfully extracted and saved to {filename}"
        except requests.exceptions.RequestException as e:
            return f"Failed to extract data {e}"

    def transform_load_context(self, file_path:str, output_folder:str, output_format:str):
        """
        Transform data from a source file and save the processed output to the target folder.

        Args:
            file_path (str): The path to the input file containing the raw data to be transformed.
            output_folder (str): The directory where the transformed data will be saved.
            output_format (str): The output file format to use, such as CSV, JSON, or Parquet.

        Returns:
            str: A message indicating the status of the transformation and load operation.
        """
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == ".csv":
            df = pd.read_csv(file_path)
        elif file_extension == ".json":
            df = pd.read_json(file_path, lines=True)
        elif file_extension == ".parquet":  
            df = pd.read_parquet(file_path)
        else:
            return f"Unsupported file format: {file_extension}"

        top_3_rows = df.head(3)
        return top_3_rows

    def execute_code(self, code:str):
        """
        Execute a given Python code string and return the result.

        Args:
            code (str): The Python code to be executed.
            
        Returns:
            str: The result of the executed code.
        """
        try:
            exec(code)
            return "Code executed successfully."
        except Exception as e:
            return f"Error executing code: {e}"
        

if __name__ =="__main__":

    obj=ETLTools()

    # print(obj.extract_load("https://pokeapi.co/api/v2/pokemon/","data/extract","csv"))

    path="/home/shivam/sandbox/Dataagent/data/extract/Extracted_data.csv"
    print(obj.transform_load_context(path, "data/transform", "csv"))