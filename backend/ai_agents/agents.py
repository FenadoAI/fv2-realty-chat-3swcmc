# Extensible AI agents with LangChain and MCP support

from typing import Dict, Any, Optional, List
import os
import logging
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from pydantic import BaseModel

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    # AI agent configuration
    api_base_url: str = None
    model_name: str = None
    api_key: str = None
    
    def __post_init__(self):
        # Load from env if not provided
        if self.api_base_url is None:
            self.api_base_url = os.getenv("LITELLM_BASE_URL", "https://litellm-docker-545630944929.us-central1.run.app")
        if self.model_name is None:
            self.model_name = os.getenv("AI_MODEL_NAME", "gemini-2.5-pro")
        if self.api_key is None:
            # LITELLM_AUTH_TOKEN for AI API
            self.api_key = os.getenv("LITELLM_AUTH_TOKEN", "dummy-key")


class AgentResponse(BaseModel):
    # Standard response format
    success: bool
    content: str
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None


class BaseAgent:
    # Base AI agent with LangChain and MCP support
    
    def __init__(self, config: AgentConfig, system_prompt: str = "You are a helpful AI assistant."):
        self.config = config
        self.system_prompt = system_prompt
        
        # LangChain ChatOpenAI setup
        self.llm = ChatOpenAI(
            base_url=config.api_base_url,
            api_key=config.api_key,
            model=config.model_name
        )
        
        # MCP client lazy init
        self.mcp_client: Optional[MultiServerMCPClient] = None
        self.mcp_tools = []
        
        logger.info(f"Initialized {self.__class__.__name__} with model {config.model_name}")
    
    def setup_mcp(self, server_configs: List[Dict[str, str]]):
        # Setup MCP servers
        try:
            self.mcp_client = MultiServerMCPClient(server_configs)
            # Tools bound when needed
            self.mcp_tools = []
            logger.info(f"MCP setup complete")
        except Exception as e:
            logger.error(f"Failed to setup MCP: {e}")
            self.mcp_client = None
    
    async def execute(self, prompt: str, use_tools: bool = True) -> AgentResponse:
        # Execute agent with prompt
        try:
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]
            
            # Use MCP tools if available
            if use_tools and self.mcp_client and self.mcp_tools:
                # Agent with tools
                agent_executor = self.llm.bind_tools(self.mcp_tools)
                response = await agent_executor.ainvoke(messages)
            else:
                # LLM without tools
                response = await self.llm.ainvoke(messages)
            
            return AgentResponse(
                success=True,
                content=response.content,
                metadata={
                    "model": self.config.model_name,
                    "tools_used": len(self.mcp_tools) if use_tools else 0
                }
            )
            
        except Exception as e:
            logger.error(f"Error executing agent: {e}")
            return AgentResponse(
                success=False,
                content="",
                error=str(e)
            )
    
    def get_capabilities(self) -> List[str]:
        # Get agent capabilities
        capabilities = ["text_generation", "conversation"]
        if self.mcp_client:
            capabilities.append("mcp_enabled")
        return capabilities


class SearchAgent(BaseAgent):
    # Web search and research agent
    
    def __init__(self, config: AgentConfig):
        system_prompt = "Research assistant with web search tools. Use search for current info, cite sources."
        
        super().__init__(config, system_prompt)
        
        # Web search MCP setup
        self.setup_web_search_mcp()
    
    def setup_web_search_mcp(self):
        # Setup web search MCP with auth token
        mcp_token = os.getenv("CODEXHUB_MCP_AUTH_TOKEN")
        if mcp_token and mcp_token != "dummy-key":
            server_configs = [{
                "type": "http",
                "url": "https://mcp.codexhub.ai/web/mcp",
                "headers": {"x-team-key": mcp_token}
            }]
            self.setup_mcp(server_configs)
            logger.info("Web search MCP configured")
        else:
            logger.warning("CODEXHUB_MCP_AUTH_TOKEN not found, web search disabled")


class ChatAgent(BaseAgent):
    # General chat and assistance agent

    def __init__(self, config: AgentConfig):
        system_prompt = "Friendly conversational AI. Natural conversations, explanations, analysis. Helpful, harmless, honest."

        super().__init__(config, system_prompt)


class RealEstateAgent(BaseAgent):
    # Specialized real estate chat agent

    def __init__(self, config: AgentConfig, db_client=None):
        self.db_client = db_client

        system_prompt = """You are an expert real estate assistant for our property listings platform.

IMPORTANT: You can ONLY discuss properties that are currently listed in our database. Do NOT discuss or recommend properties that are not in our inventory.

Your role is to help users with our listed properties by:
- Describing specific properties from our inventory
- Comparing properties in our listings
- Answering questions about features, pricing, and details of our listed properties
- Providing guidance on which of our properties might suit their needs
- General real estate advice related to buying/selling process

ALWAYS base your responses on the property data provided to you. If asked about properties not in our database, politely redirect them to browse our available listings.

Be professional, knowledgeable, and helpful while staying focused on our property inventory."""

        super().__init__(config, system_prompt)

        # Setup web search for current market data (optional)
        self.setup_real_estate_mcp()

    def setup_real_estate_mcp(self):
        # Setup web search MCP for real estate market data
        mcp_token = os.getenv("CODEXHUB_MCP_AUTH_TOKEN")
        if mcp_token and mcp_token != "dummy-key":
            server_configs = [{
                "type": "http",
                "url": "https://mcp.codexhub.ai/web/mcp",
                "headers": {"x-team-key": mcp_token}
            }]
            self.setup_mcp(server_configs)
            logger.info("Real estate web search MCP configured")
        else:
            logger.warning("CODEXHUB_MCP_AUTH_TOKEN not found, real estate web search disabled")

    async def get_properties_context(self):
        # Fetch current property listings for context
        if not self.db_client:
            return "No database connection available."

        try:
            db = self.db_client[os.getenv('DB_NAME', 'ai_agents')]
            properties = await db.properties.find({"status": "active"}).limit(50).to_list(50)

            if not properties:
                return "No active properties found in our database."

            # Format properties for AI context
            properties_text = "CURRENT PROPERTY LISTINGS:\n\n"
            for prop in properties:
                properties_text += f"""
Property: {prop.get('title', 'N/A')}
Price: ${prop.get('price', 0):,}
Location: {prop.get('location', 'N/A')}
Address: {prop.get('address', 'N/A')}
Bedrooms: {prop.get('bedrooms', 'N/A')} | Bathrooms: {prop.get('bathrooms', 'N/A')} | Size: {prop.get('sqft', 'N/A')} sqft
Type: {prop.get('property_type', 'N/A')}
Description: {prop.get('description', 'N/A')}
Amenities: {', '.join(prop.get('amenities', []))}
MLS: {prop.get('mls_number', 'N/A')}
---"""

            return properties_text

        except Exception as e:
            logger.error(f"Error fetching properties context: {e}")
            return "Unable to fetch current property listings."

    async def execute(self, prompt: str, use_tools: bool = True) -> AgentResponse:
        # Execute agent with property context
        try:
            # Get current property listings
            properties_context = await self.get_properties_context()

            # Enhanced prompt with property context
            enhanced_prompt = f"""{properties_context}

USER QUESTION: {prompt}

Remember: Only discuss the properties listed above. If the user asks about properties not in our listings, politely redirect them to our available inventory."""

            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=enhanced_prompt)
            ]

            # Use MCP tools if available
            if use_tools and self.mcp_client and self.mcp_tools:
                # Agent with tools
                agent_executor = self.llm.bind_tools(self.mcp_tools)
                response = await agent_executor.ainvoke(messages)
            else:
                # LLM without tools
                response = await self.llm.ainvoke(messages)

            return AgentResponse(
                success=True,
                content=response.content,
                metadata={
                    "model": self.config.model_name,
                    "tools_used": len(self.mcp_tools) if use_tools else 0,
                    "properties_count": properties_context.count("Property:") if properties_context else 0
                }
            )

        except Exception as e:
            logger.error(f"Error executing real estate agent: {e}")
            return AgentResponse(
                success=False,
                content="",
                error=str(e)
            )

    def get_capabilities(self) -> List[str]:
        capabilities = super().get_capabilities()
        capabilities.extend([
            "real_estate_expertise",
            "property_listings",
            "property_comparison",
            "inventory_focused"
        ])
        return capabilities
