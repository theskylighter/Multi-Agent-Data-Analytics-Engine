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

            filename = os.path.join(output_folder, f"Extracted data.{format}")
            os.makedirs(output_folder, exist_ok=True)
            # write the data
            df  = pd.json_normalize(data["results"])
            if format=="csv":
                df.to_csv(filename,index=False)
            elif format=="json":
                df.to_json(filename, orient="records", lines=True)
            elif format=="parquet":
                df.to_json(filename, index=False)
            else:
                return f"Unsupported format: {format}"
            return f" Data successfully extracted and saved to {filename}"
        except requests.exceptions.RequestException as e:
            return f"Failed to extract data {e}"

    def transform_load_context(self, file_path:str, output_folder:str, format:str):
        """
        
        """
if __name__ =="__main__":

    obj=ETLTools()
    print(obj.extract_load("https://pokeapi.co/api/v2/pokemon/","data/extract","csv"))