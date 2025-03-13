

def createdb(conn):
    personal_word_dict = {
        'Мир': 'Peace',
        'Белый': 'White',
        'Зеленый': 'Green',
        'Красный': 'Red',
        'Привет': 'Hello',
        'Машина': 'Car',
        'Он': 'He',
        'Мы': 'We',
        'Она': 'She',
        'Дом': 'House',
    }

    common_words = {
        1: ['White', 'Green', 'Hello', 'We'],
        2: ['House', 'Car', 'Green', 'Red'],
        3: ['Red', 'Hello', 'Car', 'He'],
        4: ['Hello', 'Car', 'He', 'We'],
        5: ['Car', 'He','We', 'She'],
        6: ['He', 'We', 'She', 'House'],
        7: ['We', 'She', 'House', 'Peace'],
        8: ['She', 'House', 'Peace', 'White'],
        9: ['House', 'Peace', 'White', 'Green'],
        10: ['Peace', 'White', 'Green', 'Red'],
    }
    with conn.cursor() as cur:
        for key, value in personal_word_dict.items():
            cur.execute("""
                INSERT INTO personal_words (user_id,russian,english) VALUES (%s, %s, %s);
                        """, ('1', key, value))
        conn.commit()
        for key, value in common_words.items():
            for val in value:
                cur.execute("""
                    INSERT INTO common_words (word_id, english) VALUES (%s, %s);
                            """, (key, val))
        conn.commit()