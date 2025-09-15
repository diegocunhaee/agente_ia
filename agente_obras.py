import json
import os
from datetime import datetime
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class AgenteObras:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        
        with open('dados.json', 'r', encoding='utf-8') as f:
            self.dados = json.load(f)
        
        self.system_prompt = """Você é um especialista em análise de custos de obras.
        Analise orçamentos e identifique oportunidades de economia.
        Seja prático e objetivo. Responda sempre em português brasileiro."""
    
    def analisar_orcamento(self, orcamento):

        total = sum(item['quantidade'] * item['preco'] for item in orcamento)
        
        contexto = self._buscar_dados_relevantes(orcamento)
        
        prompt = f"""
        ORÇAMENTO:
        {self._formatar_orcamento(orcamento)}
        Total: R$ {total:,.2f}
        
        DADOS DE REFERÊNCIA:
        {contexto}
        
        Analise e forneça:
        1. Principais oportunidades de economia
        2. Alertas sobre preços fora do mercado
        3. Economia estimada em R$ e % em tabela
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    
    def consultar_item(self, item_nome):
        """Consulta informações sobre um item específico"""
        dados_item = self._buscar_dados_relevantes([{"item": item_nome}])
        
        prompt = f"""
        CONSULTA SOBRE: {item_nome}
        
        DADOS DISPONÍVEIS:
        {dados_item}
        
        Forneça informações sobre:
        - Preço de mercado
        - Dicas de economia
        - Alertas importantes
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
    
    def _buscar_dados_relevantes(self, orcamento):
        """Busca dados relevantes na base"""
        contexto = ""
        
        for item_orc in orcamento:
            nome = item_orc['item'].lower()
            
            for dado in self.dados:
                if any(tag in nome or nome in tag for tag in dado.get('tags', [])):
                    contexto += f"\n• {dado['item']}: R$ {dado.get('preco_referencia', 0):.2f}"
                    if 'dicas_economia' in dado:
                        contexto += f" - {dado['dicas_economia'][0]}"
                    break
        
        return contexto or "Nenhum dado de referência específico encontrado."
    
    def _formatar_orcamento(self, orcamento):
        """Formata orçamento para exibição"""
        texto = ""
        for item in orcamento:
            nome = item['item']
            qtd = item['quantidade']
            preco = item['preco']
            total = qtd * preco
            texto += f"- {nome}: {qtd} x R$ {preco:.2f} = R$ {total:.2f}\n"
        return texto
    
    def salvar_orcamento_excel(self, orcamento, analise_ia=None, nome_arquivo=None):
        """Salva orçamento em planilha Excel"""
        if nome_arquivo is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"orcamento_{timestamp}.xlsx"
        
        dados_orcamento = []
        for item in orcamento:
            preco_ref = self._buscar_preco_referencia(item['item'])
            total = item['quantidade'] * item['preco']
            economia_potencial = (item['preco'] - preco_ref) * item['quantidade'] if preco_ref > 0 else 0
            
            dados_orcamento.append({
                'Item': item['item'],
                'Quantidade': item['quantidade'],
                'Preço Unitário': item['preco'],
                'Preço Referência': preco_ref,
                'Subtotal': total,
                'Economia Potencial': economia_potencial,
                'Status': 'Acima do mercado' if item['preco'] > preco_ref and preco_ref > 0 else 'Normal'
            })
        
        df = pd.DataFrame(dados_orcamento)
        
        total_geral = df['Subtotal'].sum()
        economia_total = df['Economia Potencial'].sum()
        
        df.loc[len(df)] = ['TOTAL', '', '', '', total_geral, economia_total, '']
        
        with pd.ExcelWriter(nome_arquivo, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Orçamento', index=False)
            
            if analise_ia:
                df_analise = pd.DataFrame({
                    'Análise da IA': [analise_ia],
                    'Data': [datetime.now().strftime("%d/%m/%Y %H:%M")]
                })
                df_analise.to_excel(writer, sheet_name='Análise IA', index=False)
            
            df_referencias = pd.DataFrame(self.dados)
            df_referencias.to_excel(writer, sheet_name='Referências', index=False)
        
        return nome_arquivo
    
    def salvar_orcamento_simples(self, orcamento, nome_arquivo=None):
        """Salva apenas o orçamento sem análise"""
        if nome_arquivo is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"orcamento_simples_{timestamp}.xlsx"
        
        dados = []
        for item in orcamento:
            total = item['quantidade'] * item['preco']
            dados.append({
                'Item': item['item'],
                'Quantidade': item['quantidade'],
                'Preço Unitário': f"R$ {item['preco']:.2f}",
                'Subtotal': f"R$ {total:.2f}"
            })
        
        total_geral = sum(item['quantidade'] * item['preco'] for item in orcamento)
        dados.append({
            'Item': 'TOTAL',
            'Quantidade': '',
            'Preço Unitário': '',
            'Subtotal': f"R$ {total_geral:.2f}"
        })
        
        df = pd.DataFrame(dados)
        df.to_excel(nome_arquivo, index=False)
        
        return nome_arquivo
    
    def _buscar_preco_referencia(self, item_nome):
        """Busca preço de referência na base"""
        nome_lower = item_nome.lower()
        
        for dado in self.dados:
            if any(tag in nome_lower or nome_lower in tag for tag in dado.get('tags', [])):
                return dado.get('preco_referencia', 0)
        
        return 0