"""
    Generic algorithms for data structure processing, etc.
"""
from itertools import groupby

##
#  Generic matrix and vector processing tasks.
##


def index_vector(v):
    """
        Return an index for values in the given sequence
        >>> index_vector( (9, 8, 7))
        {9: 0, 8: 1, 7: 2}
    """
    return { v[i] : i for i in range(len(v)) }


def sparse_to_full_vector(sparse_vector, col_index, key, empty_value=None):
    """
        Return a full vector from the given sparse vector, filling empty cells with the empty_value.
        :param sparse_vector a linear sequence, sorted by key
        :param col_index an index for key values (maps key values onto column indicies of full vector)
        :param key callable that returns key from vector element to perform lookup for column index
        :return len(cols) list populated from values in sparse_vector

        >>> sparse_v = [ {'row':'a', 'col':'ii'}, {'row':'a', 'col':'iv'}, ]
        >>> col_index = index_vector( ('i','ii','iii','iv') )
        >>> sparse_to_full_vector(sparse_v, col_index, lambda el: el['col'])
        [None, {'row': 'a', 'col': 'ii'}, None, {'row': 'a', 'col': 'iv'}]
    """
    full_row = [empty_value] * len(col_index)
    for el in sparse_vector :
        full_row[col_index[key(el)]] = el
    return full_row


def sparse_to_full_matrix(sparse_matrix, row_index, row_key, col_index, col_key, empty_value=None):
    """
        Return a full matrix from the given sparse matrix, filling empty cells with the empty_value.
        :param sparse_matrix in a linear sequence, sorted by col_key within row_key (row-major sort)
        :param row_index an index for row_key values (maps row_key values onto row indicies)
        :param row_key callable that returns key from matrix element to index rows with
        :param col_index an index for col_key values (maps col_key values onto column indicies)
        :param col_key callable that returns key from matrix element to index columns with
        :return len(rows) x len(cols) matrix (row-major list of lists) populated from sparse_matrix

        >>> sparse = [
        ...    {'row':'a', 'col':'ii'}, {'row':'a', 'col':'iii'},
        ...    {'row':'b', 'col':'ii'},
        ...
        ...    {'row':'d', 'col':'i'}, {'row':'d', 'col':'iii'},
        ...    {'row':'e', 'col':'i'}, {'row':'e', 'col':'ii'}, {'row':'e', 'col':'iii'},
        ...]
        >>> sparse_to_full_matrix(sparse, index_vector( ('a','b','c','d','e') ), lambda el: el['row'], index_vector( ('i','ii','iii',) ), lambda el: el['col'])
        [[None, {'row': 'a', 'col': 'ii'}, {'row': 'a', 'col': 'iii'}], [None, {'row': 'b', 'col': 'ii'}, None], [None, None, None], [{'row': 'd', 'col': 'i'}, None, {'row': 'd', 'col': 'iii'}], [{'row': 'e', 'col': 'i'}, {'row': 'e', 'col': 'ii'}, {'row': 'e', 'col': 'iii'}]]
    """
    empty_row = [empty_value]*len(col_index)
    sparse_rows = { row : sparse_to_full_vector(sparse_row, col_index, col_key, empty_value)
                                          for row, sparse_row in groupby(sparse_matrix, row_key)}
    full_matrix =  []
    for key in row_index:
        full_matrix.append(sparse_rows.get(key, empty_row))
    return full_matrix

