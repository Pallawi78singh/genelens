import json
from datetime import datetime, timezone

def run_pipeline(gene_name):
    gene_name = gene_name.strip().upper()
    print(f'\n{"="*55}')
    print(f'  🧬 Running pipeline for: {gene_name}')
    print(f'{"="*55}')

    result = {
        'gene':                      gene_name,
        'timestamp':                 datetime.now(timezone.utc).isoformat(),
        'uniprot_id':                None,
        'protein_name':              None,
        'organism':                  None,
        'sequence_length':           None,
        'alphafold_url':             None,
        'alphafold_viewer_url':      None,
        'alphafold_structure_exists': False,
        'alphafold_model_date':      None,
        'drugs':                     [],
        'drug_count':                0,
        'errors':                    {},
    }

        try:
        uni = fetch_uniprot_data(gene_name)
        result.update({
            'uniprot_id':      uni['uniprot_id'],
            'protein_name':    uni['protein_name'],
            'organism':        uni['organism'],
            'sequence_length': uni['sequence_length'],
        })
        print(f'\n✅ UniProt   → {uni["uniprot_id"]} | {uni["protein_name"]}')
    except Exception as e:
        result['errors']['uniprot'] = str(e)
        print(f'\n❌ UniProt   → {e}')


    if result['uniprot_id']:
        try:
            af = get_alphafold_data(result['uniprot_id'])
            result.update({
                'alphafold_structure_exists': af['structure_exists'],
                'alphafold_url':             af['pdb_url'],
                'alphafold_viewer_url':      af['viewer_url'],
                'alphafold_model_date':      af['model_date'],
            })
            icon = '✅' if af['structure_exists'] else '⚠️ '
            print(f'{icon} AlphaFold  → {"Structure found" if af["structure_exists"] else "No structure available"}')
        except Exception as e:
            result['errors']['alphafold'] = str(e)
            print(f'❌ AlphaFold → {e}')
    else:
        result['errors']['alphafold'] = 'Skipped: UniProt failed.'
        print('⏭️  AlphaFold  → Skipped')

  
    try:
        drugs = fetch_drug_interactions(gene_name)
        result['drugs']      = drugs['drugs']
        result['drug_count'] = drugs['unique_drugs']
        print(f'✅ DGIdb     → {drugs["unique_drugs"]} unique drugs ({drugs["total_raw"]} raw interactions)')
    except Exception as e:
        result['errors']['drugdb'] = str(e)
        print(f'❌ DGIdb     → {e}')

    print(f'\n{"="*55}')
    return result