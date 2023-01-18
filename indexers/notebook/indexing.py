from elasticsearch_dsl import Index
import os

import pandas as pd

from elasticsearch import Elasticsearch

from .. import utils


# ----------------------------------------------------------------------------------

class ElasticsearchIndexer():
    '''Index preprocessed notebooks with Elasticsearch.

    Attrs:
        - es: Elasticsearch client
        - index_name: Elasticsearch index name.
        - notebook_path: The path for storing notebook files.
        - source_name: 'Kaggle' or 'Github'. The repository source for notebooks
        - doc_type: 'preprocessed' or 'raw'. The document type for notebooks
    '''

    def __init__(
            self, es: Elasticsearch, source_name: str, doc_type: str,
            index_name: str, id_key: str,
            ):
        self.es = es
        self.source_name = source_name
        self.doc_type = doc_type
        self.index_name = index_name
        self.id_key = id_key

        self.notebook_path = os.path.join(
            os.path.dirname(__file__),
            f'data/{self.source_name}/notebook_lists',
            )
        if doc_type == 'raw':
            source_file_name = 'updated_processed_notebooks.csv'
        elif doc_type == 'preprocessed':
            source_file_name = 'raw_notebooks.csv'
        else:
            raise ValueError(f'unknown doc_type: {doc_type}')
        self.source_file_name = os.path.join(
            self.notebook_path,
            source_file_name
            )

    def generate_index_files(self) -> list:
        ''' Generate a list of index files to be indexed by Elasticsearch.

        Each index file is in the form of dictionary.
        Depending on the source name, the index uses different schema.
        '''
        indexfiles = []
        # Index preprocessed notebooks
        if self.doc_type == 'preprocessed':
            # ['source_id', 'name', 'file_name', 'html_url', 'description', 'source', 'docid', 'language',
            # 'num_cells', 'num_code_cells', 'num_md_cells', 'len_md_text']
            df_notebooks = pd.read_csv(
                os.path.join(self.notebook_path, self.source_file_name)
                )
            indexfiles = df_notebooks.to_dict('records')

        # Index raw notebooks
        # ['docid', 'source_id', 'name', 'file_name', 'source', 'notebook_source_file']
        elif self.doc_type == 'raw':
            root = self.notebook_path
            df_notebooks = pd.read_csv(
                os.path.join(self.notebook_path, self.source_file_name)
                )
            indexfiles = df_notebooks.to_dict('records')
        else:
            print("Notebook type is unknown, please specify a doc_type.")
        return indexfiles

    def index_notebooks(self, reindex=False):
        ''' Index generated files into Elasticsearch database given index name

        Can index raw notebooks and preprocessed notebooks.

        When indexing raw notebooks, it requires a `kaggle_raw_notebooks.csv` file placed under `notebook_path`
        '''
        indexer = utils.ElasticsearchIndexer(self.index_name)

        # Call Elasticsearch to index the files
        indexfiles = self.generate_index_files()
        for count, record in enumerate(indexfiles):
            print(f'Indexing {str(count + 1)}-th notebook!\n')
            indexer.ingest_record(record[self.id_key], record)
        return True


# ----------------------------------------------------------------------------------


def main():
    es = utils.create_es_client()

    indexer = ElasticsearchIndexer(
        es=es,
        source_name="Kaggle",
        doc_type="preprocessed",
        index_name="kaggle_notebooks",
        id_key="docid",
        )
    indexer.index_notebooks(reindex=False)

    indexer = ElasticsearchIndexer(
        es=es,
        source_name="Kaggle",
        doc_type="raw",
        index_name="kaggle_raw_notebooks",
        id_key="docid",
        )
    indexer.index_notebooks(reindex=False)

    # indexer = ElasticsearchIndexer(
    #     es=es,
    #     source_name="Github",
    #     doc_type="preprocessed",
    #     index_name="github_notebooks",
    #     id_key="git_url",
    #     )
    # indexer.index_notebooks(reindex=False)
    #
    # indexer = ElasticsearchIndexer(
    #     es=es,
    #     source_name="Github",
    #     doc_type="raw",
    #     index_name="github_raw_notebooks",
    #     id_key="git_url",
    #     )
    # indexer.index_notebooks(reindex=False)


if __name__ == '__main__':
    main()
