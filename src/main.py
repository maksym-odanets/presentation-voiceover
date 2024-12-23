import argparse
import tempfile
from pathlib import Path

import win32com.client

from logger import ConsoleLogger
from speech_generator import OpenAISpeechGenerator
from presentation_voiceover import PresentationVoiceover


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PowerPoint Voiceover.")
    parser.add_argument("--api-key", required=True, help="API key to access the OpenAI")
    parser.add_argument("--pptx-file", required=True, help="The path to the PowerPoint presentation")
    parser.add_argument("--audio-dir", help="The directory to store audio files")
    parser.add_argument("--no-cache", action='store_true', help="If set, the audio directory will be emptied before processing")
    parser.add_argument("--model", default="tts-1", help="Model to use for text-to-speech generation")
    parser.add_argument("--voice", default="alloy", help="Voice to use for text-to-speech generation")
    parser.add_argument("--slides", help="Comma-separated list of slide numbers to regenerate")
    return parser.parse_args()


def create_audio_dir(base_dir: str, presentation_path: str) -> Path:
    audio_dir = Path(base_dir) if base_dir and Path(base_dir).exists() else Path(tempfile.gettempdir()) / Path(presentation_path).stem
    audio_dir.mkdir(exist_ok=True)
    return audio_dir


def main() -> None:
    args = parse_arguments()

    logger = ConsoleLogger()
    tts = OpenAISpeechGenerator(args.api_key, args.model, args.voice)

    pptx_file = Path(args.pptx_file)
    if not pptx_file.exists():
        logger.error(f"File not found: {pptx_file}")
        return

    app = win32com.client.Dispatch("PowerPoint.Application")
    prs = app.Presentations.Open(str(pptx_file))

    audio_dir = create_audio_dir(args.audio_dir, args.pptx_file)
    pptx_notes_to_voiceover = PresentationVoiceover(logger, tts)

    if args.no_cache:
        tts.clear_cache(audio_dir)

    slides_to_process = [int(slide.strip()) for slide in args.slides.split(',')] if args.slides else None
    pptx_notes_to_voiceover.handle(prs, audio_dir, slides_to_process)

    modified_pptx_file = pptx_file.with_stem(f"{pptx_file.stem}_modified")
    prs.SaveAs(str(modified_pptx_file))
    prs.Close()
    app.Quit()

    logger.info(f"Saved modified presentation to {modified_pptx_file}")


if __name__ == "__main__":
    main()