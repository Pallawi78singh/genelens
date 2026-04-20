import requests
import logging

logger = logging.getLogger(__name__)

ALPHAFOLD_API  = 'https://alphafold.ebi.ac.uk/api/prediction'
AF_PDB_URL     = 'https://alphafold.ebi.ac.uk/files/AF-{uid}-F1-model_v4.pdb'
AF_VIEWER_URL  = 'https://alphafold.ebi.ac.uk/entry/{uid}'

def get_alphafold_data(uniprot_id):
    try:
        response = requests.get(f'{ALPHAFOLD_API}/{uniprot_id}', timeout=15)
    except requests.exceptions.Timeout:
        raise RuntimeError('AlphaFold API timed out.')
    except requests.exceptions.ConnectionError:
        raise RuntimeError('Cannot connect to AlphaFold EBI.')

    if response.status_code == 404:
        return {
            'structure_exists': False,
            'pdb_url':          None,
            'viewer_url':       AF_VIEWER_URL.format(uid=uniprot_id),
            'model_date':       None,
        }

    response.raise_for_status()
    entries = response.json()

    if not entries:
        return {'structure_exists': False, 'pdb_url': None,
                'viewer_url': AF_VIEWER_URL.format(uid=uniprot_id), 'model_date': None}

    top = entries[0]
    return {
        'structure_exists': True,
        'pdb_url':          top.get('pdbUrl') or AF_PDB_URL.format(uid=uniprot_id),
        'viewer_url':       AF_VIEWER_URL.format(uid=uniprot_id),
        'model_date':       top.get('modelCreatedDate', 'Unknown'),
    }
