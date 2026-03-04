"""
demo_generator.py — Generación de datos sintéticos de prueba.

Skills:
    - skill_data_validation (output compliant)

Generates realistic pharmaceutical inventory movements and kit commitments
for demonstration and testing purposes.
"""

import pandas as pd
import numpy as np
from datetime import timedelta


# ---------------------------------------------------------------------------
# Pharmaceutical product catalog (sample names)
# ---------------------------------------------------------------------------
_CATEGORIAS = [
    ("Analgésico", ["Paracetamol", "Ibuprofeno", "Diclofenaco", "Ketorolaco", "Tramadol",
                     "Naproxeno", "Metamizol", "Celecoxib", "Meloxicam", "Acetaminofén"]),
    ("Antibiótico", ["Amoxicilina", "Azitromicina", "Ciprofloxacino", "Cefalexina", "Clindamicina",
                      "Metronidazol", "Levofloxacino", "Doxiciclina", "Ampicilina", "Gentamicina"]),
    ("Antiinflamatorio", ["Dexametasona", "Prednisolona", "Betametasona", "Hidrocortisona",
                           "Prednisona", "Metilprednisolona", "Budesonida", "Fluticasona",
                           "Triamcinolona", "Deflazacort"]),
    ("Cardiovascular", ["Enalapril", "Losartán", "Amlodipino", "Atenolol", "Metoprolol",
                          "Valsartán", "Hidroclorotiazida", "Furosemida", "Espironolactona",
                          "Carvedilol"]),
    ("Gastrointestinal", ["Omeprazol", "Ranitidina", "Metoclopramida", "Loperamida",
                            "Pantoprazol", "Esomeprazol", "Lansoprazol", "Sucralfato",
                            "Domperidona", "Bismuto"]),
    ("Anestésico", ["Lidocaína", "Bupivacaína", "Propofol", "Ketamina", "Sevoflurano",
                     "Fentanilo", "Remifentanilo", "Midazolam", "Rocuronio", "Atracurio"]),
    ("Material Quirúrgico", ["Sutura Vicryl", "Sutura Seda", "Sutura Nylon", "Gasa Estéril",
                              "Vendaje Elástico", "Guante Quirúrgico", "Jeringa 10ml",
                              "Jeringa 5ml", "Catéter IV", "Sonda Foley"]),
    ("Solución IV", ["Solución Salina 0.9%", "Dextrosa 5%", "Lactato Ringer", "Solución Hartmann",
                      "Manitol 20%", "Albúmina 5%", "Gelatina Succinilada",
                      "Solución Glucosada 10%", "Bicarbonato Sodio", "Cloruro Potasio"]),
    ("Hemostático", ["Ácido Tranexámico", "Vitamina K", "Protamina", "Fibrinógeno",
                      "Complejo Protrombínico", "Desmopresina", "Aprotinina", "Ácido Aminocaproico",
                      "Trombina Tópica", "Celulosa Oxidada"]),
    ("Otros", ["Heparina", "Enoxaparina", "Warfarina", "Insulina NPH", "Insulina Rápida",
               "Salbutamol", "Bromuro Ipratropio", "Oxígeno Medicinal", "Adrenalina",
               "Atropina"]),
]


def _build_product_catalog(n_products: int = 500) -> pd.DataFrame:
    """Build a catalog of n pharmaceutical products with codes and names."""
    rng = np.random.default_rng(42)
    products = []

    # Flatten all names
    all_names = []
    for cat, names in _CATEGORIAS:
        for name in names:
            all_names.append((cat, name))

    # Generate enough products
    idx = 0
    while len(products) < n_products:
        cat, base_name = all_names[idx % len(all_names)]
        suffix = f" {idx // len(all_names) + 1}" if idx >= len(all_names) else ""
        concentration = rng.choice(["50mg", "100mg", "250mg", "500mg", "1g", "5ml", "10ml", "20ml", "500ml", "1L", ""])
        code = f"MED-{idx + 1001:05d}"
        full_name = f"{base_name}{suffix} {concentration}".strip()
        products.append({"codigo": code, "nombre": full_name, "categoria": cat})
        idx += 1

    return pd.DataFrame(products[:n_products])


def generate_demo_movements(
    n_products: int = 500,
    n_days: int = 90,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate realistic daily inventory movements for demonstration.

    Parameters
    ----------
    n_products : int
        Number of unique pharmaceutical products.
    n_days : int
        Number of historical days to simulate.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: fecha, codigo, nombre, bodega, tipo_movimiento, cantidad
    """
    rng = np.random.default_rng(seed)
    catalog = _build_product_catalog(n_products)

    end_date = pd.Timestamp.now().normalize()
    start_date = end_date - timedelta(days=n_days - 1)
    dates = pd.date_range(start_date, end_date, freq="D")

    records = []

    for _, product in catalog.iterrows():
        codigo = product["codigo"]
        nombre = product["nombre"]

        # Assign consumption profile: high / medium / low
        profile = rng.choice(["high", "medium", "low"], p=[0.15, 0.45, 0.40])
        if profile == "high":
            daily_mean = rng.uniform(8, 25)
        elif profile == "medium":
            daily_mean = rng.uniform(2, 8)
        else:
            daily_mean = rng.uniform(0.2, 2)

        # Determine primary warehouse
        primary_bodega = rng.choice(["1185", "1188"])
        secondary_bodega = "1188" if primary_bodega == "1185" else "1185"
        split = rng.uniform(0.5, 0.85)  # primary warehouse gets this fraction

        # Initial stock entry (day 0)
        initial_stock = int(daily_mean * rng.uniform(25, 45))
        init_primary = int(initial_stock * split)
        init_secondary = initial_stock - init_primary

        records.append({
            "fecha": start_date,
            "codigo": codigo,
            "nombre": nombre,
            "bodega": primary_bodega,
            "tipo_movimiento": "entrada",
            "cantidad": init_primary,
        })
        records.append({
            "fecha": start_date,
            "codigo": codigo,
            "nombre": nombre,
            "bodega": secondary_bodega,
            "tipo_movimiento": "entrada",
            "cantidad": init_secondary,
        })

        # Daily movements
        for day in dates:
            # Exits (consumption) — daily with noise
            salida_total = max(0, int(rng.normal(daily_mean, daily_mean * 0.3)))
            if salida_total > 0:
                salida_primary = max(0, int(salida_total * split + rng.normal(0, 1)))
                salida_secondary = max(0, salida_total - salida_primary)

                if salida_primary > 0:
                    records.append({
                        "fecha": day,
                        "codigo": codigo,
                        "nombre": nombre,
                        "bodega": primary_bodega,
                        "tipo_movimiento": "salida",
                        "cantidad": salida_primary,
                    })
                if salida_secondary > 0:
                    records.append({
                        "fecha": day,
                        "codigo": codigo,
                        "nombre": nombre,
                        "bodega": secondary_bodega,
                        "tipo_movimiento": "salida",
                        "cantidad": salida_secondary,
                    })

            # Periodic restocking (roughly every 15 days)
            if rng.random() < (1 / 15):
                restock = int(daily_mean * rng.uniform(12, 20))
                restock_bod = rng.choice([primary_bodega, secondary_bodega])
                records.append({
                    "fecha": day,
                    "codigo": codigo,
                    "nombre": nombre,
                    "bodega": restock_bod,
                    "tipo_movimiento": "entrada",
                    "cantidad": restock,
                })

    df = pd.DataFrame(records)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.sort_values(["fecha", "codigo"]).reset_index(drop=True)
    return df


def generate_demo_kits(
    df_movements: pd.DataFrame,
    fraction: float = 0.20,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate random kit commitments for a fraction of active products.

    Parameters
    ----------
    df_movements : pd.DataFrame
        Movements DataFrame (used to get product catalog).
    fraction : float
        Fraction of products with kit commitments.
    seed : int
        Random seed.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: codigo, nombre, cantidad_comprometida
    """
    rng = np.random.default_rng(seed)
    products = df_movements[["codigo", "nombre"]].drop_duplicates()
    n_kits = max(1, int(len(products) * fraction))
    kit_products = products.sample(n=n_kits, random_state=seed)

    kit_products = kit_products.copy()
    kit_products["cantidad_comprometida"] = rng.integers(5, 80, size=n_kits)

    return kit_products[["codigo", "nombre", "cantidad_comprometida"]].reset_index(drop=True)
