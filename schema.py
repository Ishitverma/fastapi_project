from pydantic import BaseModel,ConfigDict,Field,ValidationError
class Postbase(BaseModel):
    title: str= Field(min_length=1,max_length=100)
    content: str= Field(min_length=1,max_length=100)
    author: str = Field(min_length=1,max_length=50)

class PostCreate(Postbase):
    pass
    

class PostResponse(Postbase):
    model_config=ConfigDict(from_attributes=True)
    id:int
    date_posted:str
