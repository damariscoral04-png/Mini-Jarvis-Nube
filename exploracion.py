"""
MÓDULO DE EXPLORACIÓN DE LA ARQUITECTURA - TRANSFORMER - DamJar 
Tokenización, embeddings y self-attention
"""

print("="*60)
print("EXPLORACIÓN DEL MODELO - ARQUITECTURA TRANSFORMER")
print("="*60)

from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np

# ============================================================
# 1TOKENIZACIÓN — Texto → tokens numéricos
# ============================================================
print("\n 1. TOKENIZACIÓN")
print("-" * 40)
texto_prueba = "Hola, soy DamJar, asistente de Damaris. Soy un asistente basado en inteligencia artificial."
print(f"Texto de entrada: {texto_prueba}")

tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
tokens = tokenizer(texto_prueba, return_tensors="pt")

print(f"\n Tokens generados: {len(tokens['input_ids'][0])}")
print(f"IDs de tokens: {tokens['input_ids'].tolist()[0]}")
palabras_tokens = tokenizer.convert_ids_to_tokens(tokens['input_ids'][0])
print(f"Palabras/subpalabras: {palabras_tokens}")
print("👉 Explicación: El texto se divide en unidades numéricas que el modelo puede procesar.")

# ============================================================
#  EMBEDDINGS — Representación vectorial
# ============================================================
print("\n 2. EMBEDDINGS (Representación vectorial)")
print("-" * 40)
modelo = AutoModel.from_pretrained("bert-base-uncased", output_attentions=True)
salida = modelo(**tokens)

embeddings = salida.last_hidden_state
print(f"Forma del tensor de embeddings: {embeddings.shape}")
print(f"   → {embeddings.shape[1]} tokens × {embeddings.shape[2]} dimensiones")
print(" Explicación: Cada token se convierte en un vector que codifica su significado.")

# ============================================================
# SELF-ATTENTION — Conexiones entre tokens
# ============================================================
print("\n 3. SELF-ATTENTION (Mecanismo de atención)")
print("-" * 40)
pesos_atencion = salida.attentions[0][0]
print(f" Matriz de atención: {pesos_atencion.shape}")
print(" Explicación: Cada token 'mira' a los demás para entender el contexto.")
if len(palabras_tokens) >= 6:
    print(f"   Ejemplo: El token '{palabras_tokens[3]}' presta atención a '{palabras_tokens[5]}' con peso: {pesos_atencion[3,5]:.4f}")

print("\n" + "="*60)
print(" EXPLORACIÓN COMPLETA — Lista para la sustentación")
print("="*60)