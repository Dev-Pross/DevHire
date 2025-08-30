import { PrismaClient } from "@prisma/client";
import prisma from "@/app/utiles/database";


async function insert_user(data:any){
  return prisma.user.create({data})
}

async function update_row(id:string, data:{ column: string, value: string[]}){
  if(!id){
    throw new Error("id not provided")
  }
  if(!data.column){
   throw new Error("column name not provided")
  } 
  if(!data.value){
   throw new Error("value not provided")
  } 
  return prisma.user.update({
    where: { id: id},
    data:{
      [data.column] : data.value
    }
  })
}

async function fetch(id:any) {
  if(!id){
    throw new Error("id not provided")
  }
  return prisma.user.findFirst({
    where: {id}
  })
}
export async function POST(request: Request) {
  const url = new URL(request.url)
  const action = url.searchParams.get("action")
  const body = await request.json();

  try {

    switch(action){
      case "insert":
        const created = await insert_user(body)
        return new Response(JSON.stringify({success:true, user: created}),{
          status:201
        });

      case "update":
        const {id, data} = body
        const updated = await update_row(id,data)
        return new Response(JSON.stringify({success:true,  message:"row updated"}),{
          status: 200
        })
      default:
        return new Response(JSON.stringify({ success: false, message: "Invalid action" }), 
        { status: 400 });
    }
  } catch (error: any) {
    return new Response(
      JSON.stringify({ success: false, message: error.message || "Unknown error" }),
      { status: 500 }
    );
  }
}

export async function GET(request: Request){
  const url = new URL(request.url)
  const action = url.searchParams.get("id")

  try
  {

    const user = await fetch(action)
    return new Response(JSON.stringify({success: true, user:user}),{status:200})

  }catch(err: any){
    return new Response(JSON.stringify({success: false, message: err.message || "Unknown error" }),
  {
    status: 500
  })
  }


}
