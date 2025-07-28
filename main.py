from pathlib import Path
import json
import time
from src.persona_analyzer import PersonaAnalyzer
from src.utils import setup_logging, load_json_safely

def main():
    setup_logging()

    input_dir = Path("input")
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print("❌ No PDF files found in /input folder.")
        return

    config_path = input_dir / "persona_config.json"
    if not config_path.exists():
        # Create a default config file if missing
        default_config = {
            "persona": "Default Persona",
            "job_to_be_done": "Default Job"
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2)
        print("⚠️ persona_config.json not found. Created a default config.")

    print("🔍 Running Persona Analyzer (Round 1B)...")
    config = load_json_safely(config_path)
    analyzer = PersonaAnalyzer()
    result = analyzer.analyze_documents(pdf_files, config)
    with open(output_dir / "persona_analysis.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print("✅ Round 1B complete. Check output/persona_analysis.json")

if __name__ == "__main__":
    main()