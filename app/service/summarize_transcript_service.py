import requests
import json
import os
import logging

from ..config.config import Config

logger = logging.getLogger("insights-service")
logger.setLevel(logging.INFO)

class InsightsService:
    def __init__(self):
        self.config = Config()

    def analyze_transcript(self, file_path):
        """
        Analyzes a transcript file to determine risk category and justification.

        Args:
            file_path (str): The full path to the transcript file.

        Returns:
            tuple: A tuple containing (risk_category, justification) or (error_message, None).
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                transcript_content = file.read()

            prompt = f"""
            Analyze the following customer transcript to assess the risk of them not paying back their credit card dues on time.
            Based *only* on the content of this transcript, classify the customer's risk and provide a brief justification.

            Your response MUST be a valid JSON object with two keys:
            1. "category": A single word, either "HIGH", "MEDIUM", or "LOW".
            2. "justification": A brief, one-sentence explanation for your classification, citing key phrases from the transcript if possible.

            Example response format:
            {{
            "category": "HIGH",
            "justification": "The customer mentioned a recent job loss and uncertainty about making the next payment."
            }}

            Transcript:
            ---
            {transcript_content}
            ---

            JSON Response:
            """

            payload = {
                "model": self.config.MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "format": "json" # Specify JSON format for the response
            }

            response = requests.post(self.config.MODEL_GENERATE_URL, json=payload)
            response.raise_for_status()

            # The model's response is a JSON string, so we parse it into a dictionary
            response_data = response.json()
            analysis_result = json.loads(response_data.get("response", "{}"))

            category = analysis_result.get("category", "INVALID_FORMAT").strip().upper()
            justification = analysis_result.get("justification", "Model did not provide a justification.")

            if category not in ["HIGH", "MEDIUM", "LOW"]:
                return "UNEXPECTED_CATEGORY", f"Model returned an invalid category: {category}"

            return category, justification

        except FileNotFoundError:
            return "ERROR_FILE_NOT_FOUND", None
        except requests.exceptions.RequestException as e:
            return f"ERROR_OLLAMA_CONNECTION", f"Details: {e}"
        except json.JSONDecodeError:
            return "ERROR_INVALID_JSON", "The model did not return a valid JSON response."
        except Exception as e:
            return f"ERROR_UNEXPECTED", f"Details: {e}"

    def write_insight(self, filename, risk_category, justification):
        """
        Writes the analysis result and justification to a structured JSON file.

        Args:
            filename (str): The original name of the file.
            risk_category (str): The determined risk category.
            justification (str): The explanation provided by the model.
        """
        try:
            os.makedirs(self.config.DESTINATION_DIRECTORY, exist_ok=True)
            output_path = os.path.join(self.config.DESTINATION_DIRECTORY, filename)

            # Updated data structure to include the justification
            insight_data = {
                "source_file": filename,
                "risk_analysis": {
                    "category": risk_category,
                    "justification": justification,
                    "model_used": self.config.MODEL_NAME
                }
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(insight_data, f, indent=4)
            print(f" -> Insight saved to: {output_path}")

        except Exception as e:
            print(f" -> Error writing file '{output_path}': {e}")

    def generate(self):
        """
        Main function to orchestrate the analysis and file writing process.
        """
        if not os.path.isdir(self.config.SOURCE_DIRECTORY):
            print(f"Error: The source directory '{self.config.SOURCE_DIRECTORY}' does not exist.")
            return

        print(f"Starting analysis of files in: {self.config.SOURCE_DIRECTORY}")
        print(f"Results will be saved in: {self.config.DESTINATION_DIRECTORY}\n")

        for filename in os.listdir(self.config.SOURCE_DIRECTORY):
            file_path = os.path.join(self.config.SOURCE_DIRECTORY, filename)

            if os.path.isfile(file_path):
                print(f"Analyzing '{filename}'...")
                risk_category, justification = self.analyze_transcript(file_path)

                if justification is not None:
                    self.write_insight(filename, risk_category, justification)
                else:
                    # Handle cases where analysis failed
                    error_message = f"Analysis failed for '{filename}'. Reason: {risk_category}"
                    print(f" -> {error_message}")
                    # Optionally write an error file
                    self.write_insight(filename, "ANALYSIS_FAILED", risk_category)
                
                # move processed file from source to a new path self.config.processed_directory
                processed_dir = self.config.PROCESSED_DIRECTORY
                os.makedirs(processed_dir, exist_ok=True)
                new_path = os.path.join(processed_dir, filename)
                os.rename(file_path, new_path)
                
