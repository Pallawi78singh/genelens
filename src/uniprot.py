import requests
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

UNIPROT_BASE_URL = 'https://rest.uniprot.org/uniprotkb/search'
FIELDS = 'accession,protein_name,sequence,organism_name,gene_names'

def fetch_uniprot_data(gene_name, organism='Homo sapiens'):
    params = {
        'query': f'gene:{gene_name} AND organism_name:"{organism}" AND reviewed:true',
        'format': 'json',
        'fields': FIELDS,
        'size': 5,
    }
    try:
        response = requests.get(UNIPROT_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError('UniProt API timed out.')
    except requests.exceptions.ConnectionError:
        raise RuntimeError('Cannot connect to UniProt.')

    results = response.json().get('results', [])

    if not results:
        params['query'] = f'gene:{gene_name} AND organism_name:"{organism}"'
        response = requests.get(UNIPROT_BASE_URL, params=params, timeout=15)
        results = response.json().get('results', [])

    if not results:
        raise ValueError(f"Gene '{gene_name}' not found in UniProt.")

    top = results[0]
    protein_names = top.get('proteinDescription', {})
    recommended   = protein_names.get('recommendedName', {})
    full_name     = recommended.get('fullName', {}).get('value', '')
    if not full_name:
        submitted = protein_names.get('submittedNames', [{}])
        full_name = submitted[0].get('fullName', {}).get('value', 'Unknown') if submitted else 'Unknown'

    sequence_data = top.get('sequence', {})
    return {
        'uniprot_id':      top.get('primaryAccession', 'N/A'),
        'protein_name':    full_name,
        'sequence_length': sequence_data.get('length'),
        'organism':        top.get('organism', {}).get('scientificName', 'Unknown'),
    }