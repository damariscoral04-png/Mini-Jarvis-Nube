# ==================================================
# EXPLORACIÓN DE LA ARQUITECTURA TRANSFORMER
# Tokenización | Embeddings | Atención | Limitaciones
# Módulo de exploración pedido en la sección 5.1 del proyecto
# ==================================================
#
# NOTA TÉCNICA: Ollama (usado en main.py) no expone los tensores
# internos del modelo (embeddings, pesos de atención) a través de
# su API, solo el texto de entrada/salida. Por eso este módulo usa
# un modelo equivalente de Hugging Face (bert-base-uncased) que sí
# permite inspeccionar esos valores con output_attentions=True.
# El tipo de arquitectura (Transformer) y el proceso interno
# (tokenizar -> embeber -> atender -> predecir) es el mismo en ambos.

from transformers import AutoTokenizer, AutoModel
import torch

NOMBRE_MODELO = "bert-base-uncased"

print("=" * 70)
print("EXPLORACIÓN DEL MODELO - ARQUITECTURA TRANSFORMER")
print("=" * 70)

tokenizador = AutoTokenizer.from_pretrained(NOMBRE_MODELO)
modelo = AutoModel.from_pretrained(NOMBRE_MODELO, output_attentions=True)


def analizar_arquitectura(texto_prueba):
    print(f"\nFrase de entrada: {texto_prueba}")
    print("-" * 70)

    # 1. TOKENIZACIÓN ---------------------------------------------------
    # El texto se divide en unidades (tokens) que el modelo entiende
    # como números (IDs), no como palabras.
    tokens = tokenizador.tokenize(texto_prueba)
    entradas = tokenizador(texto_prueba, return_tensors="pt")
    print("\n1) TOKENIZACIÓN")
    print(f"   Tokens: {tokens}")
    print(f"   Cantidad de tokens: {len(tokens)}")
    print(f"   IDs numéricos: {entradas['input_ids'].tolist()[0]}")

    # 2, 3 y 4. EMBEDDING + ATENCIÓN + ACTUALIZACIÓN POR CONTEXTO -------
    # Cada token se convierte en un vector (embedding). Ese vector pasa
    # por varias capas de self-attention + feed-forward, donde cada
    # token "mira" a los demás tokens y actualiza su representación
    # según el contexto de la frase completa.
    with torch.no_grad():
        salidas = modelo(**entradas)
        atencion_ultima_capa = salidas.attentions[-1]

    print("\n2) EMBEDDING")
    print(f"   Dimensión del vector por token: {salidas.last_hidden_state.shape[2]}")

    print("\n3) ATENCIÓN (self-attention)")
    print(f"   Cabeceras de atención en la última capa: {atencion_ultima_capa.shape[1]}")
    print("   Cada token calcula un peso de atención hacia todos los demás tokens.")

    # 5. PREDICCIÓN CON SOFTMAX ------------------------------------------
    # En un modelo generativo, al final se aplica softmax sobre el
    # vocabulario completo para obtener la probabilidad de cada
    # palabra posible como "siguiente token".
    print("\n4) PREDICCIÓN (softmax)")
    print("   Softmax convierte los valores del modelo en probabilidades")
    print("   y se elige el token más probable como siguiente palabra.")

    # 6. REPETICIÓN ---------------------------------------------------------
    print("\n5) REPETICIÓN")
    print("   El token elegido se agrega al texto y el proceso se repite")
    print("   hasta llegar a un límite o a un token de fin de secuencia.")

    # LIMITACIONES -----------------------------------------------------------
    print("\n" + "=" * 70)
    print("LIMITACIONES DEL MODELO")
    print("=" * 70)
    print("- Alucinaciones: puede inventar información con total confianza.")
    print("- Razonamiento matemático: falla con cálculos numéricos exactos.")
    print("- Contexto largo: la atención se diluye y pierde información antigua.")
    print("- Sesgos: hereda los sesgos del corpus de entrenamiento.")
    print("- Sin memoria real: no recuerda nada fuera del contexto actual.")


if __name__ == "__main__":
    analizar_arquitectura(
        "Mini-JARVIS usa inteligencia artificial basada en la arquitectura Transformer."
    )