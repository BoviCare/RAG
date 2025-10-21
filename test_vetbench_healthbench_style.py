#!/usr/bin/env python3
"""
VetBench Testing Script using HealthBench-style evaluation
Following OpenAI HealthBench structure for veterinary medicine
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List
from vetbench_healthbench_style import VetBenchHealthBenchStyle
from model_comparison import ModelComparison
from main import app
from vector_service import VectorService
from rag import generate_rag_response, rerank_documents_with_openai

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BoviCareRAGSystemHealthBenchStyle:
    """Wrapper for BoviCare RAG system to work with HealthBench-style VetBench evaluator"""
    
    def __init__(self, vector_service, model_client):
        self.vector_service = vector_service
        self.model_client = model_client
    
    async def ask(self, query: str, use_reranking: bool = True) -> Dict[str, Any]:
        """Ask a question to the RAG system with optional reranking"""
        try:
            # Perform hybrid search (get more results for reranking)
            search_results = await self.vector_service.hybrid_search(
                query=query,
                top_k=4  # Get more results for reranking
            )
            
            if not search_results:
                return {
                    "response": "I couldn't find any relevant information about that query in our bovine disease database.",
                    "sources": []
                }
            
            # Rerank documents if requested
            if use_reranking:
                logger.info("Reranking documents with model...")
                reranked_results = await self._rerank_documents_with_model(
                    query=query,
                    documents=search_results
                )
                final_results = reranked_results[:3]  # Take top 3 after reranking
            else:
                final_results = search_results[:3]  # Take top 3 without reranking
            
            # Generate response using model client
            response_text = await self._generate_rag_response_with_model(
                query=query,
                context_docs=final_results
            )
            
            # Prepare sources
            sources = []
            for doc in final_results:
                source = {
                    "disease_name": doc.get("disease_name", "N/A"),
                    "disease_type": doc.get("disease_type", "N/A"),
                    "chunk_index": doc.get("chunk_index", "N/A"),
                    "section_type": doc.get("section_type", "N/A"),
                    "page_number": doc.get("page_number", "N/A"),
                    "relevance_score": doc.get("score", 0.0),
                    "content_preview": doc.get("section_text", "")[:200] + "..." if len(doc.get("section_text", "")) > 200 else doc.get("section_text", "")
                }
                sources.append(source)
            
            return {
                "response": response_text,
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Error in RAG system: {e}")
            return {
                "response": f"Error processing query: {str(e)}",
                "sources": []
            }
    
    async def _generate_rag_response_with_model(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """Generate RAG response using the model client"""
        try:
            # Build context from documents
            context = "\n\n".join([
                f"Document {i+1}: {doc.get('section_text', '')}"
                for i, doc in enumerate(context_docs)
            ])
            
            prompt = f"""
            You are an expert veterinary medicine Q&A assistant specializing in bovine diseases. 
            Use the following context to answer the user's question about bovine diseases.
            If the context does not contain the answer, state that you could not find the information.
            Provide accurate, helpful information based on the veterinary literature provided.

            Context:
            ---
            {context}
            ---

            Question: "{query}"
            
            Answer:
            """
            
            response = await self.model_client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are an expert veterinary medicine assistant specializing in bovine diseases. Provide accurate, helpful information based on the veterinary literature provided."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response["content"]
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            return f"Error generating response: {str(e)}"
    
    async def _rerank_documents_with_model(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rerank documents using the model client"""
        try:
            async def score_document(doc: Dict[str, Any]) -> tuple[float, Dict[str, Any]]:
                doc_text = doc.get('section_text', '')[:1000]
                
                try:
                    response = await self.model_client.chat_completion(
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": f"Rate the relevance of this document to the query from 0.0 to 1.0. Query: {query}. Document: {doc_text}. Respond with just a number."}
                        ]
                    )
                    
                    score_text = response["content"].strip()
                    
                    # Extract number from response
                    import re
                    number_match = re.search(r'(\d+\.?\d*)', score_text)
                    if number_match:
                        score = float(number_match.group(1))
                        # Ensure score is between 0.0 and 1.0
                        score = max(0.0, min(1.0, score))
                        return (score, doc)
                    else:
                        return (0.5, doc)
                        
                except Exception as e:
                    logger.error(f"Error scoring document: {e}")
                    return (0.5, doc)

            # Score all documents
            scoring_tasks = [score_document(doc) for doc in documents]
            scored_docs = await asyncio.gather(*scoring_tasks)
            
            # Sort by score (highest first)
            reranked_docs = sorted(scored_docs, key=lambda x: x[0], reverse=True)
            
            return [doc for score, doc in reranked_docs]
            
        except Exception as e:
            logger.error(f"Error in reranking: {e}")
            return documents  # Return original order if reranking fails

async def run_vetbench_healthbench_style_test(models_to_test: List[str] = None, use_reranking: bool = True):
    """Run HealthBench-style VetBench evaluation on BoviCare system with model comparison"""
    
    if models_to_test is None:
        models_to_test = ["gpt-5-mini"]  # Focus on GPT-5-mini for faster testing
    
    logger.info(f"🐄 Starting HealthBench-style VetBench evaluation for BoviCare RAG system with models: {models_to_test}")
    logger.info(f"🔄 Reranking enabled: {use_reranking}")
    
    # Initialize model comparison system
    model_comparison = ModelComparison()
    
    # Initialize components
    async with VectorService() as vector_service:
        all_results = {}
        
        for model_name in models_to_test:
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing model: {model_name}")
            logger.info(f"{'='*60}")
            
            # Create model client
            model_client = model_comparison.create_model_client(model_name)
            
            # Initialize RAG system with this model
            rag_system = BoviCareRAGSystemHealthBenchStyle(vector_service, model_client)
            
            # Initialize HealthBench-style VetBench evaluator with this model
            evaluator = VetBenchHealthBenchStyle(model_client=model_client)
        
            # Define all 10 real veterinary test queries with expected responses from veterinary experts
            test_queries = [
                {
                    "query": "Notei abortos no terço final da gestação e diminuição na produção de leite. Qual doença pode estar afetando meu rebanho e o que devo fazer?",
                    "expected_response": "Os sinais são compatíveis com Brucelose bovina, causada pela Brucella abortus. A enfermidade provoca abortos no final da gestação e queda na produção de leite. O controle baseia-se na vacinação das fêmeas entre 3 e 8 meses com a cepa B19 ou RB51, eliminação dos animais positivos e rigorosa biossegurança no manejo reprodutivo. É fundamental realizar testes sorológicos de triagem (Rosa de Bengala) e confirmação (2-mercaptoetanol ou fixação de complemento). Consulte o veterinário responsável e notifique os casos conforme o PNCEBT.",
                    "context": "disease_diagnosis"
                },
                {
                    "query": "Durante o período de chuvas, observei aumento de abortos e natimortos. Qual a provável causa e como prevenir novos casos?",
                    "expected_response": "Provavelmente trata-se de Leptospirose bovina, zoonose causada por Leptospira spp.. A transmissão ocorre em ambientes úmidos e contaminados por urina de animais infectados. O controle envolve vacinação periódica do rebanho, drenagem de áreas alagadas, controle de roedores e isolamento de animais doentes. A higienização das instalações e manejo adequado da água são medidas fundamentais.",
                    "context": "disease_outbreak"
                },
                {
                    "query": "Alguns bovinos estão com dificuldade de locomoção, salivação intensa e sinais neurológicos. O que pode ser e qual a conduta?",
                    "expected_response": "Esses sinais indicam Raiva dos herbívoros, doença viral fatal. Não há tratamento, e a profilaxia é essencial. Deve-se vacinar todo o rebanho anualmente, isolar imediatamente os animais suspeitos e notificar o serviço veterinário oficial. Evite manipular carcaças sem proteção, pois é zoonose grave. O controle dos transmissores, como morcegos hematófagos, também é indispensável.",
                    "context": "emergency_care"
                },
                {
                    "query": "Notei grumos e alteração na coloração do leite de algumas vacas. O que pode estar ocorrendo e como controlar?",
                    "expected_response": "Os sintomas sugerem Mastite, inflamação da glândula mamária geralmente causada por Staphylococcus, Streptococcus ou E. coli. O controle envolve higiene rigorosa na ordenha, descarte do primeiro jato, desinfecção dos tetos antes e após a ordenha e manutenção dos equipamentos limpos. É recomendada a terapia de vaca seca e o acompanhamento com exames de CCS (contagem de células somáticas). Casos graves requerem avaliação veterinária e tratamento com antibióticos adequados.",
                    "context": "mastitis_management"
                },
                {
                    "query": "Um animal apresentou emagrecimento progressivo e tosse crônica. Pode ser tuberculose? O que devo fazer?",
                    "expected_response": "Sim, a Tuberculose bovina, causada por Mycobacterium bovis, provoca perda de peso, tosse e debilidade geral. É uma zoonose de importância sanitária. O controle é feito pelo abate sanitário dos animais positivos identificados por testes intradérmicos (tuberculinização). Não há tratamento, e a prevenção depende de programas oficiais como o PNCEBT. Evite consumo de leite cru e mantenha isolamento dos suspeitos.",
                    "context": "disease_diagnosis"
                },
                {
                    "query": "Mesmo vacinando contra brucelose, alguns animais continuam abortando. Pode ser outra doença?",
                    "expected_response": "Sim, pode tratar-se de Neosporose bovina, causada pelo protozoário Neospora caninum. Transmite-se verticalmente e via contaminação por fezes de cães. O controle envolve impedir o acesso de cães a restos placentários e alimentos do gado, além do descarte de animais positivos. Não existe vacina ou tratamento eficaz, portanto, o manejo higiênico e a biossegurança são essenciais.",
                    "context": "disease_outbreak"
                },
                {
                    "query": "Alguns bovinos estão apáticos, com mucosas pálidas e queda de produção de leite. O que devo suspeitar?",
                    "expected_response": "Os sinais são compatíveis com Tristeza Parasitária Bovina, causada por Babesia bovis, Babesia bigemina e Anaplasma marginale, transmitidas por carrapatos. Deve-se realizar controle rigoroso de ectoparasitas e manejo integrado de pastagens. O diagnóstico é confirmado por exame de sangue e esfregaço. A prevenção é feita com controle do vetor e vacinação específica conforme recomendação veterinária.",
                    "context": "disease_diagnosis"
                },
                {
                    "query": "Há casos de corrimento nasal, febre e queda na fertilidade. O que pode ser e como agir?",
                    "expected_response": "Os sinais são característicos de Rinotraqueíte Infecciosa Bovina (IBR), causada pelo Herpesvírus bovino tipo 1. A doença afeta o trato respiratório e reprodutivo. O controle inclui vacinação regular, isolamento dos animais doentes e medidas de biossegurança para evitar disseminação. O uso de sêmen certificado livre do vírus é essencial.",
                    "context": "disease_outbreak"
                },
                {
                    "query": "Quais medidas gerais posso adotar para reduzir o risco de doenças infecciosas no rebanho?",
                    "expected_response": "A mitigação de riscos requer adoção de medidas gerais: testes sorológicos antes da compra de animais, isolamento de novos bovinos por 2–3 semanas, separação de doentes, uso de material genético livre de patógenos e higienização rigorosa das instalações. Dividir lotes por idade e condição fisiológica e manter registros sanitários são fundamentais para biossegurança e produtividade.",
                    "context": "preventive_medicine"
                },
                {
                    "query": "Como as doenças infecciosas afetam a rentabilidade da fazenda leiteira?",
                    "expected_response": "Doenças como brucelose, tuberculose e mastite geram perdas significativas: queda na produção de leite, condenação de carcaças, restrições comerciais e custos com controle e pesquisa. Programas de vacinação e biossegurança são investimentos que reduzem prejuízos a longo prazo. O equilíbrio entre prevenção e produtividade é essencial para a sustentabilidade econômica da fazenda.",
                    "context": "economic_impact"
                }
            ]
            
            logger.info(f"\n🤖 Testing Model: {model_name}")
            logger.info(f"📊 Running HealthBench-style veterinary evaluation on {len(test_queries)} test queries with {model_name}...")
            
            # Run evaluation using HealthBench-style methodology
            model_results = []
            for i, test_case in enumerate(test_queries):
                logger.info(f"🔍 Evaluating query {i+1}/{len(test_queries)}: {test_case['query'][:50]}...")
                
                # Get RAG response with reranking
                rag_response = await rag_system.ask(test_case["query"], use_reranking=use_reranking)
                actual_response = rag_response["response"]
                
                logger.info(f"   Generated response: {actual_response[:100]}...")
                logger.info(f"   Sources found: {len(rag_response['sources'])}")
                
                # Evaluate using HealthBench-style methodology
                evaluation_result = await evaluator.evaluate_veterinary_response_healthbench_style(
                    query=test_case["query"],
                    expected_response=test_case["expected_response"],
                    actual_response=actual_response,
                    context=test_case["context"]
                )
                
                logger.info(f"   VetBench Score: {evaluation_result.overall_score:.3f}")
                logger.info(f"   Rubric Items: {len(evaluation_result.rubric_items_with_grades)}")
                
                model_results.append({
                    "query": test_case["query"],
                    "expected_response": test_case["expected_response"],
                    "actual_response": actual_response,
                    "overall_score": evaluation_result.overall_score,
                    "metrics": evaluation_result.metrics,
                    "rubric_items_count": len(evaluation_result.rubric_items_with_grades),
                    "sources": rag_response["sources"]
                })
            
            # Calculate and log model performance
            average_score = sum(r["overall_score"] for r in model_results) / len(model_results)
            max_score = max(r["overall_score"] for r in model_results)
            min_score = min(r["overall_score"] for r in model_results)
            
            logger.info(f"📊 {model_client.name} Results:")
            logger.info(f"   Average Score: {average_score:.3f}")
            logger.info(f"   Best Query Score: {max_score:.3f}")
            logger.info(f"   Worst Query Score: {min_score:.3f}")
            
            # Log individual query results
            for i, result in enumerate(model_results, 1):
                logger.info(f"   Query {i}: {result['overall_score']:.3f} - {result['query'][:50]}...")
            
            # Store results for this model
            all_results[model_name] = {
                "model_name": model_client.name,
                "model_id": model_client.model_id,
                "results": model_results,
                "average_score": average_score,
                "max_score": max_score,
                "min_score": min_score
            }
        
        # Calculate final summary metrics
        best_model = max(all_results.keys(), key=lambda k: all_results[k]["average_score"])
        worst_model = min(all_results.keys(), key=lambda k: all_results[k]["average_score"])
        highest_score = max(all_results[k]["max_score"] for k in all_results)
        lowest_score = min(all_results[k]["min_score"] for k in all_results)
        
        # Log final summary
        logger.info(f"\n🏆 FINAL VETBENCH RESULTS:")
        logger.info(f"   Best Model: {best_model} ({all_results[best_model]['average_score']:.3f})")
        logger.info(f"   Worst Model: {worst_model} ({all_results[worst_model]['average_score']:.3f})")
        logger.info(f"   Score Range: {lowest_score:.3f} - {highest_score:.3f}")
        logger.info(f"   Total Queries: {len(test_queries)}")
        logger.info(f"   Reranking: {'Enabled' if use_reranking else 'Disabled'}")
        
        # Generate comprehensive report
        report = {
            "evaluation_type": "HealthBench-style VetBench Model Comparison",
            "models_tested": list(all_results.keys()),
            "total_queries": len(test_queries),
            "reranking_enabled": use_reranking,
            "model_comparison": all_results,
            "summary_metrics": {
                "best_model": best_model,
                "worst_model": worst_model,
                "score_range": {
                    "highest": highest_score,
                    "lowest": lowest_score
                }
            }
        }
        
        # Save results
        with open("vetbench_model_comparison_results.json", "w") as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*80)
        print("🐄 HEALTHBENCH-STYLE VETBENCH MODEL COMPARISON RESULTS")
        print("="*80)
        print(f"Models Tested: {', '.join(all_results.keys())}")
        print(f"Total Queries per Model: {len(test_queries)}")
        print(f"Reranking Enabled: {use_reranking}")
        
        print(f"\n📊 Model Performance Summary:")
        for model_name, model_data in all_results.items():
            print(f"\n{model_data['model_name']} ({model_name}):")
            print(f"  Average Score: {model_data['average_score']:.3f}")
            print(f"  Max Score: {model_data['max_score']:.3f}")
            print(f"  Min Score: {model_data['min_score']:.3f}")
        
        print(f"\n🏆 Best Performing Model: {report['summary_metrics']['best_model']}")
        print(f"📉 Lowest Performing Model: {report['summary_metrics']['worst_model']}")
        
        print(f"\n📄 Detailed results saved to: vetbench_model_comparison_results.json")
        print("="*80)
        
        return report

if __name__ == "__main__":
    asyncio.run(run_vetbench_healthbench_style_test())
