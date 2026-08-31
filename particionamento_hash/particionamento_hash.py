"""
Estudo de caso - Clinica Medica (180 lojas, 6 estados)
Simulacao de particionamento por HASH em uma arquitetura SEM COMPARTILHAMENTO
(shared nothing).

Ideia do experimento (bem simples):
1. "Inventamos" um dia de vendas (dado sintetico, nao real).
2. Cada venda pertence a uma loja (1 a 180).
3. Uma funcao de hash decide em qual NO (particao) essa venda vai morar.
4. Contamos quantas vendas cada no recebeu.
5. Calculamos a DISTORCAO (skew): o quanto o no mais cheio se afasta da
   media. Se a distorcao for alta, um no fica sobrecarregado e ele passa
   a definir o tempo total do processamento (isso e explicado no
   Capitulo 20, no topico de Speedup/Scaleup: "a subtarefa mais lenta
   define o tempo total do conjunto").

Este script e propositalmente simples (nivel iniciante), sem bibliotecas
externas alem da biblioteca padrao do Python.
"""

import hashlib
import random
import statistics

# ---------------------------------------------------------------
# 1) DADOS DE ENTRADA (parametros do estudo de caso, dados reais
#    do enunciado) e DADOS SIMULADOS (inventados so para o teste)
# ---------------------------------------------------------------

NUM_LOJAS = 180          # dado do enunciado (real)
NUM_ESTADOS = 6          # dado do enunciado (real)
NUM_NOS = 8               # ESTIMATIVA: quantidade de nos/particoes do
                          # cluster shared-nothing. Nao ha um numero
                          # "certo" no enunciado; 8 e apenas um valor
                          # razoavel para demonstrar o conceito.
VENDAS_POR_MINUTO_PICO = 4000   # dado do enunciado (real)
MINUTOS_SIMULADOS = 10           # ESTIMATIVA: simulamos so 10 minutos
                                  # de pico para nao gerar um arquivo gigante

random.seed(42)  # fixa a "sorte" do sorteio, so para o resultado
                  # ser sempre igual quando o script for executado de novo


def gerar_vendas_simuladas(minutos, vendas_por_minuto, num_lojas):
    """Gera uma lista de vendas falsas (simuladas).
    Cada venda e representada apenas pelo id da loja que a gerou.
    Isso e dado FICTICIO, criado so para testar o particionamento.
    """
    vendas = []
    total = minutos * vendas_por_minuto
    for i in range(total):
        loja_id = random.randint(1, num_lojas)
        vendas.append(loja_id)
    return vendas


def particao_por_hash(chave, num_nos):
    """Funcao de particionamento por hash.
    Transforma a chave (aqui, o id da loja) em um numero de 0 a num_nos-1.
    Usamos hashlib (hash estavel) em vez da funcao hash() do Python,
    porque hash() muda de valor a cada execucao do interpretador.
    """
    chave_bytes = str(chave).encode("utf-8")
    digest = hashlib.md5(chave_bytes).hexdigest()
    return int(digest, 16) % num_nos


def medir_distorcao(contagem_por_no):
    """Calcula duas medidas simples de distorcao (skew):
    - razao = carga do no mais cheio dividida pela media
    - desvio_padrao = o quanto os nos variam entre si
    Quanto mais perto de 1.0 a razao, mais equilibrado esta o cluster.
    """
    valores = list(contagem_por_no.values())
    media = statistics.mean(valores)
    maximo = max(valores)
    razao_skew = maximo / media if media > 0 else 0
    desvio_padrao = statistics.pstdev(valores)
    return media, maximo, razao_skew, desvio_padrao


def main():
    print("=" * 60)
    print("SIMULACAO: particionamento por hash - Clinica Medica")
    print("=" * 60)

    vendas = gerar_vendas_simuladas(
        MINUTOS_SIMULADOS, VENDAS_POR_MINUTO_PICO, NUM_LOJAS
    )
    print(f"Total de vendas simuladas: {len(vendas)}")
    print(f"Numero de nos (particoes) do cluster: {NUM_NOS}\n")

    # 2) Particiona cada venda por HASH DO ID DA LOJA
    contagem_por_no = {no: 0 for no in range(NUM_NOS)}
    for loja_id in vendas:
        no = particao_por_hash(loja_id, NUM_NOS)
        contagem_por_no[no] += 1

    print("Vendas recebidas por cada no:")
    for no, quantidade in sorted(contagem_por_no.items()):
        barra = "#" * (quantidade // 100)  # so para "desenhar" um grafico de texto
        print(f"  No {no}: {quantidade:5d}  {barra}")

    media, maximo, razao_skew, desvio_padrao = medir_distorcao(contagem_por_no)

    print("\nResumo da distorcao (skew):")
    print(f"  Media de vendas por no : {media:.1f}")
    print(f"  No mais cheio          : {maximo}")
    print(f"  Razao skew (max/media) : {razao_skew:.2f}")
    print(f"  Desvio padrao entre nos: {desvio_padrao:.1f}")

    print("\nComo ler o resultado:")
    print(" - Se a razao skew estiver perto de 1.0, a carga esta bem")
    print("   distribuida entre os nos (bom sinal).")
    print(" - Se algum no ficar muito acima da media, ele vira o gargalo:")
    print("   o processamento so termina quando o no mais lento terminar.")


if __name__ == "__main__":
    main()
