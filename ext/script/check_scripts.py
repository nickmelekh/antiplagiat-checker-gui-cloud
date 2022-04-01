import pandas as pd
import numpy as np
from scipy.spatial import distance 

def Levenshtein_distance(dataframe):

    # выделение списка идентификаторов студентов в отдельный список из датафрейма
    source = dataframe['hash_value'].tolist()
    result_dataframe = pd.DataFrame({'File': source[:]})

    # словарь, хранящий строку токенов. Ключ - название файла
    sequences = {}
    # токены для создания последовательности лексем
    tokens = {'for': 'C',
              'while': 'C',
              'break': 'C',
              'continue': 'C',
              '+': 'O',
              '-': 'O',
              '*': 'O',
              '**': 'O',
              '/': 'O',
              '//': 'O',
              '%': 'O',
              '=': 'O',
              '+=': 'S',
              '-=': 'S',
              '/=': 'S',
              '*=': 'S',
              '==': 'S',
              'and': 'L',
              'or': 'L',
              'not': 'L',
              'in': 'L',
              'input': 'K',
              'def': 'K',
              'import': 'K',
              'print': 'K',
              'if': 'I',
              'else': 'I',
              'elif': 'I',
              '()': 'F',
              '[': 'F',
              ']': 'F'}

    def base_add(dictionary, key, value):
        # функция добавления значений в словарь
        if key not in dictionary:
            dictionary[key] = key
            dictionary[key] = value
        else:
            dictionary[value][key] += value
        print(dictionary)
        return dictionary

    def base_sequences(dictionary, key, value):
        # создание словаря для лексем и файлов
        if key not in dictionary:
            dictionary[key] = key
            dictionary[key] = value
        else:
            dictionary[key] = value

        return dictionary

    def fish(array, stroka_1, stroka_2):
        # алгоритм Вагнера-Фишера
        numm_1 = 0
        numm_2 = 0
        for letter_1 in stroka_1:
            numm_1 += 1
            numm_2 = 0
            for letter_2 in stroka_2:
                numm_2 += 1
                if letter_1 == letter_2:
                    array[numm_1, numm_2] = array[numm_1 - 1, numm_2 - 1]
                else:
                    array[numm_1, numm_2] = min(array[numm_1 - 1, numm_2 - 1], array[numm_1, numm_2 - 1], array[numm_1 - 1, numm_2]) + 1
        return (1 - (array[-1][-1] / max(numm_1, numm_2))) * 100

    #создание матрицы для расчета расстояния Левенштейна
    def matrix(source_1, source_2):
        a = np.zeros((len(sequences[source_1]) + 1, len(sequences[source_2]) + 1), int)
        if (len(a) > 1):
            a[0] = range(len(a[1]))
            for i in range(len(sequences[source_1]) + 1):
                a[i, 0] = i
        
        return a

    #составление последовательности лексем на основании токенов
    for item in dataframe['hash_value']:

        line = dataframe.loc[dataframe['hash_value']==item].index[0]
        print(item, line)
        stroka = ''
        for word in dataframe['task_code'][line]:
            if word in tokens:
                stroka += tokens[word]
                print('found token: ' + str(word) + ' Stroka: ' + stroka)

        print(item, stroka)

        base_sequences(sequences, item, stroka)

    for i in range(len(source)):

        key_1, value_1 = source[i], sequences[source[i]]
        print(source[i], sequences[source[i]])
        result = []
        for g in range(len(source)):
            key_2, value_2 = source[g], sequences[source[g]]
            a = matrix(key_1, key_2)
            result.append(round(fish(a, sequences[key_1], sequences[key_2]), 2))

        result_dataframe[key_1] = result

    return result_dataframe


def Shingle(dataframe):

    # выделение списка идентификаторов студентов в отдельный список из датафрейма
    source = dataframe['hash_value'].tolist()
    # создание пустого датафрейма для передачи расчитанных значений
    result_dataframe = pd.DataFrame({'File': source[:]})

    # функция которая делает важные вещи
    def genshingle(source):
        import binascii
        shingleLen = 5 #длина шингла
        out = []
        for i in range(len(source)-(shingleLen-1)):
            out.append(binascii.crc32(' '.join( [x for x in source[i:i+shingleLen]] ).encode('utf-8')))
        return out

    # сравнение двух файлов
    def compare(source1, source2):
        same = 0
        for i in range(len(source1)):
            if source1[i] in source2:
                same = same + 1
        try:
            result = same * 100 / (float(max(len(source1), len(source2))))
        except:
            result = same
        return result

    # попарное сравнение кодов и запись результата в датафрейм
    for i in range(len(source)):
        key_1 = source[i]
        t1 = ' '.join(dataframe['task_code'][i])
        print('t1', t1)
        cmp1 = genshingle(t1)
        result = []
        for j in range(len(source)):
            t2 = ' '.join(dataframe['task_code'][j])
            # print('t2', t2)
            cmp2 = genshingle(t2)
            # print(cmp1, cmp2)
            result.append(round(compare(cmp1, cmp2), 2))
        print('result', result)
        result_dataframe[key_1] = result

    return result_dataframe


def Cosine_distance(dataframe):

    # выделение списка идентификаторов студентов в отдельный список из
    # датафрейма
    source = dataframe['hash_value'].tolist()
    # создание пустого датафрейма для передачи расчитанных значений
    result_dataframe = pd.DataFrame({'File': source[:]})

    #словарь уникальных слов
    uniq_words = {}
    i = 0
    for item in dataframe['task_code']:
        for word in item:
            if word not in uniq_words:
                uniq_words[word] = i
                i += 1
            else:
                pass

    #словарь всех слов, встречающихся в предложениях предложение: слово:
    # количество повторов
    ds = {}
    i = 0
    for item in dataframe['task_code']:
        dw = {}
        for word in item:
            if uniq_words[word] not in dw:
                dw[uniq_words[word]] = uniq_words[word]
                dw[uniq_words[word]] = 1
            else:
                dw[uniq_words[word]] += 1
        ds[i] = dw
        i += 1

    matrix = np.zeros((len(source), len(uniq_words)))
    for i in ds.keys():
        for j in sorted(ds[i].keys()):
            matrix[i, j] = ds[i][j]

    #косинусное расстояние между первым(нулевым) и каждым следующим предложением текста
    for i in range(len(source)):
        key_1 = source[i]
        result = []
        for j in range(len(source)):
            result.append(round((1 / (distance.cosine(matrix[i], matrix[j]) + 0.01)), 2))
        result_dataframe[key_1] = result

    return result_dataframe

def pysimilar():
    pass