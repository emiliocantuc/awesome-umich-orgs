import requests, json, re, argparse, time
import tiktoken
import numpy as np

def get_first_n_orgs(n):
    """
    Gets info for first n student orgs (ordered alphanumerically) from
    maizepages.umich.edu. Returns a list of dicts with an individual org's info.
    """

    params = {
        'orderBy[0]': 'UpperName asc',
        'top': str(n),
        'filter': '',
        'query': '',
        'skip': '',
    }

    response = requests.get(
        'https://maizepages.umich.edu/api/discovery/search/organizations',
        params=params,
    )

    if response.status_code != 200 or '@odata.context' not in response.text:
        raise Exception('Error scrapping org data')
    
    return response.json()


def process_data(raw_data):
    """
    Transforms retrieved data into final form to be stored in.
    """

    remove_html_tags = lambda s:re.sub(re.compile('<.*?>'), '', s)

    # Only fields we conserve
    conserve_fields = ['Id', 'Name', 'WebsiteKey', 'ProfilePicture', 'Description', 'Summary', 'CategoryIds']

    # Id -> Name
    categories = {}

    data = {}
    for student_info in raw_data:

        # Remove unnecessary fields and html tags 
        filtered_info = {
            k:(remove_html_tags(v) if type(v) == str else v)
            for k, v in student_info.items() if k in conserve_fields
        }

        # Build categories dict
        for _id, name in zip(student_info['CategoryIds'], student_info['CategoryNames']):
            categories[_id] = name
        
        # In case they don't have a description
        if filtered_info['Description'] is None:
            filtered_info['Description'] = filtered_info['Summary']

        data[filtered_info['Id']] = filtered_info
    
    return data, categories


def embedding_input(info):
    """
    How student org's name and description joined before embedding.
    """
    return f'{info["Name"]}: {info["Description"]}'


def get_embedding(l, key, model = 'text-embedding-ada-002'):
    """
    Calls OpenAPI's embedding API to embed string `s`.
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + key,
    }

    json_data = {
        'input': l,
        'model': model,
    }

    response = requests.post('https://api.openai.com/v1/embeddings', headers=headers, json=json_data)

    if response.status_code != 200 or 'embedding' not in response.text:
        raise Exception(f'Error getting embedding: {response.text}')
    
    return [i['embedding'] for i in response.json()['data']]



def get_batch_embeddings(l, k, tpm = 100000):
    
    num_tokens_from_string = lambda s, enc: len(tiktoken.get_encoding(enc).encode(s))
    
    embeddings = []
    i = 0
    
    # Build a request with max tokens under tpm
    while len(embeddings) < len(l):
        
        tokens = 0
        inp = []
        while tokens < tpm and i < len(l):
            inp.append(l[i])
            tokens += num_tokens_from_string(l[i], 'cl100k_base')
            i += 1
            
        if tokens > tpm:
            inp.pop()
            i -= 1
        
        if not inp: break

        tokens = sum(num_tokens_from_string(i, 'cl100k_base') for i in inp)
        print(f'Making API request with info for {len(inp)} orgs ({tokens} tokens)')
        
        # Make request here
        tmp = get_embedding(inp, k)
        embeddings.extend(tmp)
        print(f'Got {len(tmp)} embeddings!')
        
        if len(embeddings) < len(l):
            print('Sleeping 65s to abide by tpm')
            time.sleep(65)
    
    return embeddings


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', help = 'OpenAI API key')
    parser.add_argument('-N', type = int, help = 'N closest neighbors to find')
    args = parser.parse_args()
    k, N = args.k, args.N

    # Get student org raw data
    n = get_first_n_orgs(10)['@odata.count']
    print(f'Trying to get data for {n} orgs ...')

    raw_data = get_first_n_orgs(n)['value']
    print(f'Got data for {len(raw_data)} orgs from maizepages!')

    # Clean and process data
    processed_data, categories = process_data(raw_data)

    # Get embeddings
    sorted_ids = sorted(processed_data.keys())
    embed_content = [embedding_input(processed_data[i]) for i in sorted_ids]
    embeddings = get_batch_embeddings(embed_content, k = k)
    store_embeddings = {}
    for _id, emb in zip(sorted_ids, embeddings):
        store_embeddings[_id] = emb
    
    # Delete description from data - to make js file lighter
    processed_data = {
        k: {k2:v2 for k2, v2 in v.items() if k2 != 'Description'}
        for k, v in processed_data.items()
    }

    # Find closests `n` neighbors for each org
    print(f'Finding n = {N} closest neighbors ...')
    ids = np.array([k for k in processed_data]) 
    embeddings = np.array([np.array(store_embeddings[i]) for i in ids])
    for ix, _id in enumerate(ids):
        closest_ixs = np.argsort(np.array([embeddings[ix].dot(i) for i in embeddings]))[-(N+1):]
        assert closest_ixs[-1] == ix
        closest_ixs = closest_ixs[:-1][::-1]
        closest_ids = ids[closest_ixs]
        processed_data[_id]['Closest'] = closest_ids.tolist()
    
    # Write
    with open('data.js', 'w+') as f:
        for var, val in zip(['org_data', 'categories', 'updated'], [processed_data, categories, str(time.time()*1000)]):
            f.write(f'let {var}={json.dumps(val, indent = 4)}\n')
    
    with open('embeddings.json','w+') as f:
        f.write(json.dumps(store_embeddings))
    
    # Because why not
    with open('raw_data.json','w+') as f:
        f.write(json.dumps(raw_data, indent=4))
    
    print('Done')