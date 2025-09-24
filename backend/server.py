from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime

# AI agents
from ai_agents.agents import AgentConfig, SearchAgent, ChatAgent, RealEstateAgent


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# AI agents init
agent_config = AgentConfig()
search_agent: Optional[SearchAgent] = None
chat_agent: Optional[ChatAgent] = None
real_estate_agent: Optional[RealEstateAgent] = None

# Main app
app = FastAPI(title="AI Agents API", description="Minimal AI Agents API with LangGraph and MCP support")

# API router
api_router = APIRouter(prefix="/api")


# Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Property models
class Property(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    price: int  # Price in dollars
    location: str
    address: str
    bedrooms: int
    bathrooms: int
    sqft: int
    property_type: str  # "house", "condo", "apartment", "townhouse"
    status: str = "active"  # "active", "sold", "pending"
    image_url: str
    amenities: List[str] = Field(default_factory=list)
    year_built: Optional[int] = None
    garage: Optional[int] = None
    lot_size: Optional[float] = None
    mls_number: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PropertyCreate(BaseModel):
    title: str
    description: str
    price: int
    location: str
    address: str
    bedrooms: int
    bathrooms: int
    sqft: int
    property_type: str
    image_url: str
    amenities: List[str] = Field(default_factory=list)
    year_built: Optional[int] = None
    garage: Optional[int] = None
    lot_size: Optional[float] = None
    mls_number: Optional[str] = None

class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    location: Optional[str] = None
    address: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    sqft: Optional[int] = None
    property_type: Optional[str] = None
    status: Optional[str] = None
    image_url: Optional[str] = None
    amenities: Optional[List[str]] = None
    year_built: Optional[int] = None
    garage: Optional[int] = None
    lot_size: Optional[float] = None
    mls_number: Optional[str] = None


# AI agent models
class ChatRequest(BaseModel):
    message: str
    agent_type: str = "chat"  # "chat", "search", or "real_estate"
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    success: bool
    response: str
    agent_type: str
    capabilities: List[str]
    metadata: dict = Field(default_factory=dict)
    error: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    max_results: int = 5


class SearchResponse(BaseModel):
    success: bool
    query: str
    summary: str
    search_results: Optional[dict] = None
    sources_count: int
    error: Optional[str] = None

# Routes
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]


# AI agent routes
@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    # Chat with AI agent
    global search_agent, chat_agent, real_estate_agent

    try:
        # Init agents if needed
        if request.agent_type == "search" and search_agent is None:
            search_agent = SearchAgent(agent_config)

        elif request.agent_type == "chat" and chat_agent is None:
            chat_agent = ChatAgent(agent_config)

        elif request.agent_type == "real_estate" and real_estate_agent is None:
            real_estate_agent = RealEstateAgent(agent_config, client)

        # Select agent
        if request.agent_type == "search":
            agent = search_agent
        elif request.agent_type == "real_estate":
            agent = real_estate_agent
        else:
            agent = chat_agent
        
        if agent is None:
            raise HTTPException(status_code=500, detail="Failed to initialize agent")
        
        # Execute agent
        response = await agent.execute(request.message)
        
        return ChatResponse(
            success=response.success,
            response=response.content,
            agent_type=request.agent_type,
            capabilities=agent.get_capabilities(),
            metadata=response.metadata,
            error=response.error
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return ChatResponse(
            success=False,
            response="",
            agent_type=request.agent_type,
            capabilities=[],
            error=str(e)
        )


@api_router.post("/search", response_model=SearchResponse)
async def search_and_summarize(request: SearchRequest):
    # Web search with AI summary
    global search_agent
    
    try:
        # Init search agent if needed
        if search_agent is None:
            search_agent = SearchAgent(agent_config)
        
        # Search with agent
        search_prompt = f"Search for information about: {request.query}. Provide a comprehensive summary with key findings."
        result = await search_agent.execute(search_prompt, use_tools=True)
        
        if result.success:
            return SearchResponse(
                success=True,
                query=request.query,
                summary=result.content,
                search_results=result.metadata,
                sources_count=result.metadata.get("tools_used", 0)
            )
        else:
            return SearchResponse(
                success=False,
                query=request.query,
                summary="",
                sources_count=0,
                error=result.error
            )
            
    except Exception as e:
        logger.error(f"Error in search endpoint: {e}")
        return SearchResponse(
            success=False,
            query=request.query,
            summary="",
            sources_count=0,
            error=str(e)
        )


@api_router.get("/agents/capabilities")
async def get_agent_capabilities():
    # Get agent capabilities
    try:
        capabilities = {
            "search_agent": SearchAgent(agent_config).get_capabilities(),
            "chat_agent": ChatAgent(agent_config).get_capabilities(),
            "real_estate_agent": RealEstateAgent(agent_config, client).get_capabilities()
        }
        return {
            "success": True,
            "capabilities": capabilities
        }
    except Exception as e:
        logger.error(f"Error getting capabilities: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Property CRUD routes
@api_router.post("/properties", response_model=Property)
async def create_property(property_data: PropertyCreate):
    property_obj = Property(**property_data.dict())
    result = await db.properties.insert_one(property_obj.dict())
    return property_obj

@api_router.get("/properties", response_model=List[Property])
async def get_properties(
    status: str = "active",
    property_type: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    bedrooms: Optional[int] = None,
    limit: int = 100
):
    query = {"status": status}

    if property_type:
        query["property_type"] = property_type
    if min_price is not None:
        query.setdefault("price", {})["$gte"] = min_price
    if max_price is not None:
        query.setdefault("price", {})["$lte"] = max_price
    if bedrooms is not None:
        query["bedrooms"] = bedrooms

    properties = await db.properties.find(query).limit(limit).to_list(limit)
    return [Property(**prop) for prop in properties]

@api_router.get("/properties/{property_id}", response_model=Property)
async def get_property(property_id: str):
    property_data = await db.properties.find_one({"id": property_id})
    if not property_data:
        raise HTTPException(status_code=404, detail="Property not found")
    return Property(**property_data)

@api_router.put("/properties/{property_id}", response_model=Property)
async def update_property(property_id: str, property_data: PropertyUpdate):
    existing_property = await db.properties.find_one({"id": property_id})
    if not existing_property:
        raise HTTPException(status_code=404, detail="Property not found")

    update_data = {k: v for k, v in property_data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()

    await db.properties.update_one({"id": property_id}, {"$set": update_data})
    updated_property = await db.properties.find_one({"id": property_id})
    return Property(**updated_property)

@api_router.delete("/properties/{property_id}")
async def delete_property(property_id: str):
    result = await db.properties.delete_one({"id": property_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Property not found")
    return {"message": "Property deleted successfully"}

@api_router.post("/seed-properties")
async def seed_properties():
    # Check if properties already exist
    existing_count = await db.properties.count_documents({})
    if existing_count > 0:
        return {"message": f"Properties already exist ({existing_count} found). Skipping seed."}

    sample_properties = [
        {
            "title": "Modern Luxury Villa",
            "description": "Stunning modern villa with breathtaking views, premium finishes, and state-of-the-art amenities. Features an open-concept design with floor-to-ceiling windows, gourmet kitchen, and expansive outdoor living space.",
            "price": 2850000,
            "location": "Beverly Hills, CA",
            "address": "1234 Beverly Drive, Beverly Hills, CA 90210",
            "bedrooms": 5,
            "bathrooms": 4,
            "sqft": 4200,
            "property_type": "house",
            "image_url": "https://images.unsplash.com/photo-1613977257363-707ba9348227?w=600&h=400&fit=crop&crop=center",
            "amenities": ["Pool", "Spa", "Wine Cellar", "Home Theater", "Gym", "Smart Home"],
            "year_built": 2021,
            "garage": 3,
            "lot_size": 0.75,
            "mls_number": "BH2024001"
        },
        {
            "title": "Downtown Penthouse",
            "description": "Luxurious penthouse in the heart of Manhattan with panoramic city views. Features premium finishes, floor-to-ceiling windows, and access to building's exclusive amenities including rooftop terrace and concierge services.",
            "price": 1200000,
            "location": "Manhattan, NY",
            "address": "567 Park Avenue, New York, NY 10022",
            "bedrooms": 3,
            "bathrooms": 2,
            "sqft": 2100,
            "property_type": "condo",
            "image_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=600&h=400&fit=crop&crop=center",
            "amenities": ["Doorman", "Rooftop Deck", "Gym", "Storage", "Laundry"],
            "year_built": 2018,
            "garage": 1,
            "mls_number": "NY2024002"
        },
        {
            "title": "Seaside Retreat",
            "description": "Charming coastal home with direct beach access and stunning ocean views. Perfect for those seeking a peaceful retreat with modern comforts and beachside living at its finest.",
            "price": 950000,
            "location": "Malibu, CA",
            "address": "789 Pacific Coast Highway, Malibu, CA 90265",
            "bedrooms": 4,
            "bathrooms": 3,
            "sqft": 3200,
            "property_type": "house",
            "image_url": "https://images.unsplash.com/photo-1571939228382-b2f2b585ce15?w=600&h=400&fit=crop&crop=center",
            "amenities": ["Beach Access", "Ocean View", "Deck", "Fireplace", "Updated Kitchen"],
            "year_built": 2015,
            "garage": 2,
            "lot_size": 0.5,
            "mls_number": "ML2024003"
        },
        {
            "title": "Historic Brownstone",
            "description": "Beautifully restored historic brownstone in prime Brooklyn location. Combines original architectural details with modern updates. Perfect blend of character and contemporary living.",
            "price": 875000,
            "location": "Brooklyn, NY",
            "address": "123 Brooklyn Heights Promenade, Brooklyn, NY 11201",
            "bedrooms": 3,
            "bathrooms": 2,
            "sqft": 2800,
            "property_type": "townhouse",
            "image_url": "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=600&h=400&fit=crop&crop=center",
            "amenities": ["Original Details", "Garden", "Updated Kitchen", "Hardwood Floors"],
            "year_built": 1920,
            "garage": 0,
            "lot_size": 0.15,
            "mls_number": "BK2024004"
        },
        {
            "title": "Mountain View Estate",
            "description": "Spectacular estate home with panoramic mountain views and luxurious amenities. Situated on a private lot with extensive outdoor living spaces and premium finishes throughout.",
            "price": 1650000,
            "location": "Aspen, CO",
            "address": "456 Alpine Drive, Aspen, CO 81611",
            "bedrooms": 6,
            "bathrooms": 5,
            "sqft": 5500,
            "property_type": "house",
            "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600&h=400&fit=crop&crop=center",
            "amenities": ["Mountain Views", "Hot Tub", "Fireplace", "Ski Storage", "Wine Cellar", "Guest House"],
            "year_built": 2019,
            "garage": 4,
            "lot_size": 2.0,
            "mls_number": "AS2024005"
        },
        {
            "title": "Urban Loft",
            "description": "Contemporary loft in converted warehouse with exposed brick, high ceilings, and industrial charm. Located in trendy arts district with walkable access to galleries, restaurants, and nightlife.",
            "price": 625000,
            "location": "Austin, TX",
            "address": "789 Industrial Blvd, Austin, TX 78701",
            "bedrooms": 2,
            "bathrooms": 2,
            "sqft": 1800,
            "property_type": "condo",
            "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=600&h=400&fit=crop&crop=center",
            "amenities": ["Exposed Brick", "High Ceilings", "Modern Appliances", "Rooftop Access"],
            "year_built": 2017,
            "garage": 1,
            "mls_number": "AU2024006"
        }
    ]

    properties = []
    for prop_data in sample_properties:
        property_obj = Property(**prop_data)
        properties.append(property_obj.dict())

    result = await db.properties.insert_many(properties)
    return {"message": f"Successfully seeded {len(result.inserted_ids)} properties"}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    # Initialize agents on startup
    global search_agent, chat_agent, real_estate_agent
    logger.info("Starting AI Agents API...")

    # Lazy agent init for faster startup
    logger.info("AI Agents API ready!")


@app.on_event("shutdown")
async def shutdown_db_client():
    # Cleanup on shutdown
    global search_agent, chat_agent, real_estate_agent

    # Close MCP
    if search_agent and search_agent.mcp_client:
        # MCP cleanup automatic
        pass
    if real_estate_agent and real_estate_agent.mcp_client:
        # MCP cleanup automatic
        pass

    client.close()
    logger.info("AI Agents API shutdown complete.")
