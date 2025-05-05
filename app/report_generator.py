import pandas as pd

def generate_report(df, entity_ids):
    df_filtered = df[df['entity_id'].isin(entity_ids)]

    summary = df_filtered.groupby('entity_id')[
        ['visa fees', 'mastercard fees', 'visa sales', 'mastercard sales']
    ].sum()

    total = summary.sum().to_frame().T
    total.index = ['TOTAL']

    return pd.concat([summary, total])