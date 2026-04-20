DGIDB_URL  = 'https://dgidb.org/api/graphql'
DRUG_QUERY = '''
query GetDrugInteractions($gene: String!) {
  genes(names: [$gene]) {
    nodes {
      name
      interactions {
        drug { name approved }
        interactionScore
        interactionTypes { type }
        sources { sourceDbName }
        publications { pmid }
      }
    }
  }
}
'''

def fetch_drug_interactions(gene_name):
    try:
        response = requests.post(
            DGIDB_URL,
            json={'query': DRUG_QUERY, 'variables': {'gene': gene_name.upper()}},
            headers={'Content-Type': 'application/json'},
            timeout=20,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError('DGIdb API timed out.')
    except requests.exceptions.ConnectionError:
        raise RuntimeError('Cannot connect to DGIdb.')

    data = response.json()
    if 'errors' in data:
        raise RuntimeError('DGIdb GraphQL error: ' + str(data['errors']))

    nodes = data.get('data', {}).get('genes', {}).get('nodes', [])
    if not nodes:
        return {'unique_drugs': 0, 'total_raw': 0, 'drugs': []}

    interactions = nodes[0].get('interactions', [])
    seen = {}
    for item in interactions:
        drug  = item.get('drug', {})
        name  = drug.get('name', '').strip()
        if not name:
            continue
        key   = name.lower()
        score = item.get('interactionScore') or 0.0
        types   = [t.get('type') for t in (item.get('interactionTypes') or [])]
        sources = [s.get('sourceDbName') for s in (item.get('sources') or [])]
        pmids   = [str(p.get('pmid')) for p in (item.get('publications') or []) if p.get('pmid')]
        if key not in seen or score > seen[key]['interaction_score']:
            seen[key] = {
                'name':              name,
                'approved':          drug.get('approved', False),
                'interaction_score': round(score, 4),
                'interaction_types': list(set(types)),
                'sources':           list(set(sources)),
                'pubmed_ids':        pmids[:5],
            }

    drug_list = sorted(seen.values(), key=lambda d: d['interaction_score'], reverse=True)
    return {'unique_drugs': len(drug_list), 'total_raw': len(interactions), 'drugs': drug_list}
