import os
import sys
import time
import logging
import argparse
import torch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Test local Whisper model")
    parser.add_argument("--model", default="tiny", choices=["tiny", "base", "small", "medium", "large"],
                       help="Whisper model size to use")
    parser.add_argument("--audio", default=None, help="Path to audio file to transcribe")
    parser.add_argument("--device", default="cpu", help="Device to use (cuda, cpu, mps)")
    args = parser.parse_args()
    
    # Check if audio file exists
    if args.audio and not os.path.exists(args.audio):
        logger.error(f"Audio file not found: {args.audio}")
        return 1
    
    # Determine device
    if args.device:
        device = args.device
    elif torch.cuda.is_available():
        device = "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        # Force CPU for now due to MPS issues with Whisper
        logger.info("MPS is available but using CPU due to compatibility issues")
        device = "cpu"
    else:
        device = "cpu"
    
    logger.info(f"Using device: {device}")
        
    try:
        # Import whisper and load model
        import whisper
        logger.info(f"Loading Whisper model: {args.model}")
        start_time = time.time()
        
        cache_dir = os.path.expanduser("~/.cache/whisper")
        os.makedirs(cache_dir, exist_ok=True)
        
        model = whisper.load_model(
            args.model,
            device=device,
            download_root=cache_dir
        )
        
        load_time = time.time() - start_time
        logger.info(f"Model loaded in {load_time:.2f}s")
        
        # Check model info
        logger.info(f"Model size: {model.dims.n_text_ctx}")
        logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters())/1e6:.1f}M")
        
        # Transcribe audio if provided
        if args.audio:
            logger.info(f"Transcribing audio file: {args.audio}")
            start_time = time.time()
            
            result = model.transcribe(args.audio)
            
            transcribe_time = time.time() - start_time
            logger.info(f"Transcription completed in {transcribe_time:.2f}s")
            
            # Print transcription
            logger.info("Transcription:")
            logger.info(result["text"])
            
            # Print segments
            if len(result["segments"]) > 0:
                logger.info("\nSegments:")
                for segment in result["segments"]:
                    logger.info(f"[{segment['start']:.1f}s -> {segment['end']:.1f}s] {segment['text']}")
                    
            return 0
        else:
            logger.info("No audio file provided. Model loaded successfully.")
            return 0
            
    except ImportError as e:
        logger.error(f"Failed to import Whisper: {e}")
        logger.error("Please install Whisper: pip install openai-whisper")
        return 1
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 