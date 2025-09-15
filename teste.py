from agente_obras import AgenteObras

def main():
    agente = AgenteObras()
    
    orcamento = [
        {"item": "Cimento", "quantidade": 50, "preco": 35.00},
        {"item": "Areia", "quantidade": 10, "preco": 50.00},
        {"item": "Brita", "quantidade": 8, "preco": 55.00},
        {"item": "Bloco cerâmico", "quantidade": 1000, "preco": 0.65}
    ]
    
    try:
        resultado = agente.analisar_orcamento(orcamento)
        print(resultado)
        
        nome_arquivo = agente.salvar_orcamento_excel(orcamento, resultado)
        print(f"\nSalvo em: {nome_arquivo}")
        
    except Exception as e:
        print(f"Erro: {e}")
    
    print("\nComandos: 'salvar simples', 'salvar completo', 'sair' ou faça perguntas")
    
    while True:
        pergunta = input("\n> ").strip()
        
        if pergunta.lower() in ['sair', 'exit', 'quit']:
            break
        
        elif pergunta.lower() == 'salvar simples':
            try:
                nome = agente.salvar_orcamento_simples(orcamento)
                print(f"Salvo: {nome}")
            except Exception as e:
                print(f"Erro: {e}")
        
        elif pergunta.lower() == 'salvar completo':
            try:
                resultado_completo = agente.analisar_orcamento(orcamento)
                nome = agente.salvar_orcamento_excel(orcamento, resultado_completo)
                print(f"Salvo: {nome}")
            except Exception as e:
                print(f"Erro: {e}")
        
        elif pergunta:
            try:
                resposta = agente.consultar_item(pergunta)
                print(resposta)
            except Exception as e:
                print(f"Erro: {e}")

if __name__ == "__main__":
    main()