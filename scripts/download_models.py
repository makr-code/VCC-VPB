"""
BERT Model Pre-Download Script
================================

Pre-downloads embedding models to avoid first-run latency.
Part of v1.0.1 Hotfix - Performance Optimization.

Usage:
    python scripts/download_models.py
    python scripts/download_models.py --model deutsche-telekom/gbert-base

Autor: VPB Development Team
Datum: 18. Oktober 2025
"""

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def download_sentence_transformer_model(model_name: str, cache_dir: str = None):
    """
    Download SentenceTransformer model from HuggingFace
    
    Args:
        model_name: HuggingFace model identifier (e.g., "deutsche-telekom/gbert-base")
        cache_dir: Optional custom cache directory
    """
    try:
        from sentence_transformers import SentenceTransformer
        
        logger.info(f"📥 Downloading model: {model_name}")
        logger.info(f"   This may take a few minutes on first run...")
        
        # Initialize model (downloads automatically if not cached)
        model = SentenceTransformer(model_name, cache_folder=cache_dir)
        
        logger.info(f"✅ Model downloaded successfully!")
        logger.info(f"   Model name: {model_name}")
        logger.info(f"   Max sequence length: {model.max_seq_length}")
        logger.info(f"   Embedding dimension: {model.get_sentence_embedding_dimension()}")
        
        # Test embedding generation
        logger.info(f"🧪 Testing embedding generation...")
        test_text = "Test process for embedding generation"
        embedding = model.encode(test_text)
        logger.info(f"   Generated embedding shape: {embedding.shape}")
        
        return True
        
    except ImportError:
        logger.error("❌ sentence-transformers not installed!")
        logger.error("   Install with: pip install sentence-transformers")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error downloading model: {e}")
        return False


def download_all_models(cache_dir: str = None):
    """Download all required models"""
    models = [
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",  # Multilingual (incl. German) BERT
        # Alternative: "deutsche-telekom/gbert-base" (not available on HuggingFace Hub)
    ]
    
    logger.info(f"📦 Downloading {len(models)} model(s)...")
    logger.info(f"=" * 60)
    
    success_count = 0
    for model_name in models:
        logger.info(f"\n[{success_count + 1}/{len(models)}] Processing: {model_name}")
        if download_sentence_transformer_model(model_name, cache_dir):
            success_count += 1
        logger.info(f"-" * 60)
    
    logger.info(f"\n🎉 Download complete: {success_count}/{len(models)} successful")
    return success_count == len(models)


def verify_models():
    """Verify that all required models are available"""
    try:
        from sentence_transformers import SentenceTransformer
        
        logger.info("🔍 Verifying installed models...")
        
        models = [
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        ]
        
        all_available = True
        for model_name in models:
            try:
                logger.info(f"   Checking: {model_name}")
                model = SentenceTransformer(model_name)
                logger.info(f"   ✅ Available (dim: {model.get_sentence_embedding_dimension()})")
            except Exception as e:
                logger.error(f"   ❌ Not available: {e}")
                all_available = False
        
        if all_available:
            logger.info("✅ All models verified!")
        else:
            logger.error("❌ Some models missing. Run download_models.py to install.")
        
        return all_available
        
    except ImportError:
        logger.error("❌ sentence-transformers not installed!")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Download BERT models for VPB embedding generation"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Specific model to download (default: all models)"
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default=None,
        help="Custom cache directory for models"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify installed models instead of downloading"
    )
    
    args = parser.parse_args()
    
    logger.info("🚀 VPB Model Download Tool - v1.0.1")
    logger.info("=" * 60)
    
    if args.verify:
        success = verify_models()
    elif args.model:
        success = download_sentence_transformer_model(args.model, args.cache_dir)
    else:
        success = download_all_models(args.cache_dir)
    
    if success:
        logger.info("\n✅ Success! Models are ready for use.")
        logger.info("   Expected performance: 30-50 records/second")
        sys.exit(0)
    else:
        logger.error("\n❌ Download failed. Please check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
