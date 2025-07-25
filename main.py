from pathlib import Path
import json
import time
from src.structure_extractor import StructureExtractor
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

    # Check for persona config (for Round 1B)
    config_path = input_dir / "persona_config.json"
    if config_path.exists():
        print("🔍 Detected persona config. Running Round 1B...")
        from src.persona_analyzer import PersonaAnalyzer
        config = load_json_safely(config_path)
        analyzer = PersonaAnalyzer()
        result = analyzer.analyze_documents(pdf_files, config)
        with open(output_dir / "persona_analysis.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print("✅ Round 1B complete. Check output/persona_analysis.json")
    else:
        print("📘 Running Round 1A: PDF Outline Extraction...")
        extractor = StructureExtractor()
        for pdf_file in pdf_files:
            print(f"➡️  Processing {pdf_file.name}...")  # already present

            result = extractor.extract_structure(pdf_file)  # structure extraction
            print(f"🧪 Result: {result}")  # ✅ Debug line added

            out_file = output_dir / f"{pdf_file.stem}.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)

            print(f"✅ Saved: {out_file.name}")

if __name__ == "__main__":
    main()
