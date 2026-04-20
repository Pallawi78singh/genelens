import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.uniprot import fetch_uniprot_data
from src.alphafold import get_alphafold_data
from src.drugdb import fetch_drug_interactions

logger = logging.getLogger(__name__)

CACHE_FILE = Path.home() / ".gene_drug_cache.json"
CACHE_TTL_HOURS = 24


def run_pipeline(gene_name: str, use_cache: bool = True) -> dict:
    gene_name = gene_name.strip().upper()
    logger.info(f"=== Pipeline start: {gene_name} ===")

    if use_cache:
        cached = _cache_get(gene_name)
        if cached:
            logger.info(f"Cache hit for {gene_name}")
            cached["_cached"] = True
            return cached

    result = {
        "gene": gene_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uniprot_id": None,
        "protein_name": None,
        "organism": None,
        "sequence_length": None,
        "alphafold_url": None,
        "alphafold_viewer_url": None,
        "alphafold_structure_exists": False,
        "alphafold_model_date": None,
        "drugs": [],
        "drug_count": 0,
        "errors": {},
        "_cached": False,
    }

    # Stage 1: UniProt
    try:
        uniprot_data = fetch_uniprot_data(gene_name)
        result["uniprot_id"] = uniprot_data["uniprot_id"]
        result["protein_name"] = uniprot_data["protein_name"]
        result["organism"] = uniprot_data["organism"]
        result["sequence_length"] = uniprot_data.get("sequence_length")
        logger.info(f"UniProt OK: {result['uniprot_id']}")
    except Exception as e:
        logger.error(f"UniProt failed: {e}")
        result["errors"]["uniprot"] = str(e)

    # Stage 2: AlphaFold
    if result["uniprot_id"]:
        try:
            af_data = get_alphafold_data(result["uniprot_id"])
            result["alphafold_structure_exists"] = af_data["structure_exists"]
            result["alphafold_url"] = af_data["pdb_url"]
            result["alphafold_viewer_url"] = af_data["viewer_url"]
            result["alphafold_model_date"] = af_data.get("model_created_date")
            logger.info(f"AlphaFold OK: {af_data['structure_exists']}")
        except Exception as e:
            logger.error(f"AlphaFold failed: {e}")
            result["errors"]["alphafold"] = str(e)
    else:
        result["errors"]["alphafold"] = "Skipped: UniProt lookup failed."

    # Stage 3: Drugs
    try:
        drug_data = fetch_drug_interactions(gene_name)
        result["drugs"] = drug_data["drugs"]
        result["drug_count"] = drug_data["unique_drugs"]
        logger.info(f"Drugs OK: {result['drug_count']} found")
    except Exception as e:
        logger.error(f"Drug lookup failed: {e}")
        result["errors"]["drugdb"] = str(e)

    if use_cache and not result["errors"]:
        _cache_set(gene_name, result)

    logger.info(f"=== Pipeline complete: {gene_name} ===")
    return result


def _load_cache() -> dict:
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(cache: dict) -> None:
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not write cache: {e}")


def _cache_get(gene_name: str) -> Optional[dict]:
    cache = _load_cache()
    entry = cache.get(gene_name)
    if not entry:
        return None
    age_hours = (time.time() - entry.get("_cached_at", 0)) / 3600
    if age_hours > CACHE_TTL_HOURS:
        return None
    return entry.get("data")


def _cache_set(gene_name: str, data: dict) -> None:
    cache = _load_cache()
    cache[gene_name] = {"_cached_at": time.time(), "data": data}
    _save_cache(cache)
  
