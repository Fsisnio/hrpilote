import React from 'react';
import Layout from '../components/Layout';

type Tool = { name: string; vendor: string; category: string; description: string; url: string };

const tools: Tool[] = [
  { name: 'OpenAI ChatGPT', vendor: 'OpenAI', category: 'Generative AI', description: 'Conversational assistance, drafting, code help.', url: 'https://chat.openai.com' },
  { name: 'Microsoft Copilot', vendor: 'Microsoft', category: 'Productivity', description: 'AI assistance across M365 apps and Edge.', url: 'https://copilot.microsoft.com' },
  { name: 'GitHub Copilot', vendor: 'GitHub', category: 'Developer', description: 'AI code completion and pair programming.', url: 'https://github.com/features/copilot' },
  { name: 'Google Gemini', vendor: 'Google Cloud', category: 'Generative AI', description: 'Multimodal reasoning and content creation.', url: 'https://gemini.google.com' },
  { name: 'Vertex AI', vendor: 'Google Cloud', category: 'ML Platform', description: 'Build, deploy, and manage ML models.', url: 'https://cloud.google.com/vertex-ai' },
  { name: 'Amazon Bedrock', vendor: 'AWS', category: 'Generative AI', description: 'Foundation models via API for enterprise apps.', url: 'https://aws.amazon.com/bedrock/' },
  { name: 'AWS SageMaker', vendor: 'AWS', category: 'ML Platform', description: 'End-to-end ML development and MLOps.', url: 'https://aws.amazon.com/sagemaker/' },
  { name: 'Azure OpenAI Service', vendor: 'Microsoft Azure', category: 'Generative AI', description: 'Enterprise-grade access to OpenAI models.', url: 'https://azure.microsoft.com/products/ai-services/openai-service' },
  { name: 'Cohere', vendor: 'Cohere', category: 'NLP', description: 'Embeddings, classify, and generate text.', url: 'https://cohere.com' },
  { name: 'Anthropic Claude', vendor: 'Anthropic', category: 'Generative AI', description: 'Helpful, honest, and harmless assistant.', url: 'https://claude.ai' },
  { name: 'Databricks Mosaic AI', vendor: 'Databricks', category: 'Data + AI', description: 'Lakehouse-native GenAI tooling.', url: 'https://www.databricks.com/product/mosaic-ai' },
  { name: 'Snowflake Cortex', vendor: 'Snowflake', category: 'Data + AI', description: 'AI functions and apps inside Snowflake.', url: 'https://www.snowflake.com/en/data-cloud/cortex/' },
  { name: 'LangChain', vendor: 'LangChain', category: 'Framework', description: 'Framework for building LLM-powered apps.', url: 'https://langchain.com' },
  { name: 'LlamaIndex', vendor: 'LlamaIndex', category: 'Framework', description: 'Data framework for RAG applications.', url: 'https://www.llamaindex.ai' },
  { name: 'Pinecone', vendor: 'Pinecone', category: 'Vector DB', description: 'Managed vector database for retrieval.', url: 'https://www.pinecone.io' },
  { name: 'Weaviate', vendor: 'Weaviate', category: 'Vector DB', description: 'Open-source vector database.', url: 'https://weaviate.io' },
  { name: 'Milvus', vendor: 'Zilliz', category: 'Vector DB', description: 'High-performance vector database.', url: 'https://milvus.io' },
  { name: 'Hugging Face', vendor: 'Hugging Face', category: 'Models/Hub', description: 'Models, datasets, and Inference Endpoints.', url: 'https://huggingface.co' },
  { name: 'Weights & Biases', vendor: 'W&B', category: 'MLOps', description: 'Experiment tracking and model management.', url: 'https://wandb.ai' },
  { name: 'MLflow', vendor: 'Databricks (OSS)', category: 'MLOps', description: 'Model tracking, registry, and deployment.', url: 'https://mlflow.org' },
  { name: 'Kubeflow', vendor: 'Community', category: 'MLOps', description: 'Kubernetes-native ML toolkit.', url: 'https://www.kubeflow.org' },
  { name: 'DataRobot', vendor: 'DataRobot', category: 'AutoML', description: 'Automated machine learning for enterprise.', url: 'https://www.datarobot.com' },
  { name: 'H2O Driverless AI', vendor: 'H2O.ai', category: 'AutoML', description: 'AutoML for tabular and time-series.', url: 'https://www.h2o.ai/platform/driverless-ai/' },
  { name: 'Azure Cognitive Search', vendor: 'Microsoft Azure', category: 'Search', description: 'Enterprise search with vector capabilities.', url: 'https://azure.microsoft.com/products/cognitive-search' },
  { name: 'Elastic Search + ESRE', vendor: 'Elastic', category: 'Search', description: 'Search, analytics, and retrieval for RAG.', url: 'https://www.elastic.co' },
  { name: 'OpenSearch', vendor: 'AWS', category: 'Search', description: 'Search and vector search (Open Source).', url: 'https://opensearch.org' },
  { name: 'Alteryx', vendor: 'Alteryx', category: 'Analytics', description: 'Low-code analytics and automation.', url: 'https://www.alteryx.com' },
  { name: 'Power BI + Copilot', vendor: 'Microsoft', category: 'BI + AI', description: 'BI with natural language insights.', url: 'https://powerbi.microsoft.com' },
  { name: 'Looker + Gemini', vendor: 'Google Cloud', category: 'BI + AI', description: 'BI platform with generative assistance.', url: 'https://looker.com' },
  { name: 'Tableau + Einstein', vendor: 'Salesforce', category: 'BI + AI', description: 'Analytics with AI-driven insights.', url: 'https://www.tableau.com' },
];

const AITools: React.FC = () => {
  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Tools (Top 30)</h1>
          <p className="text-gray-600">Curated list of widely used, enterprise-ready AI platforms and frameworks. No external links; static overview only.</p>
        </div>

        <div className="bg-white rounded-lg shadow">
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {tools.map((t) => (
                <div key={t.name} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <h3 className="text-md font-semibold text-gray-900">{t.name}</h3>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700">{t.category}</span>
                  </div>
                  <div className="text-sm text-gray-500 mt-1">Vendor: {t.vendor}</div>
                  <p className="text-sm text-gray-700 mt-2">{t.description}</p>
                  <div className="mt-3">
                    <a
                      href={t.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-block text-sm px-3 py-1 rounded-md bg-indigo-600 text-white hover:bg-indigo-700"
                    >
                      Visit
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default AITools;


