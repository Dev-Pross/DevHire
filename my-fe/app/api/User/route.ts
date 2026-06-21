import prisma from "@/app/utiles/database";
import { Prisma } from "@prisma/client";


async function insert_user(data:any){
  return prisma.user.create({data})
}

async function update_row(id:string, data:{ column: string, value: any}){
  if(!id){
    throw new Error("id not provided")
  }
  if(!data.column){
   throw new Error("column name not provided")
  }
  if(data.value === undefined){
   throw new Error("value not provided")
  }
  // A null value clears the column. Prisma rejects a bare JS null for a Json
  // column, so translate it to the DB-null token.
  const value = data.value === null ? Prisma.DbNull : data.value;
  return prisma.user.update({
    where: { id: id},
    data:{
      [data.column] : value
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

      case "resume_uploaded": {
        // Atomically replace the resume URL and wipe the stale parsed profile
        // so the backend re-parses the new resume on the next pipeline run.
        const { id: resumeUserId, resume_url } = body;
        if (!resumeUserId) throw new Error("id not provided");
        if (!resume_url) throw new Error("resume_url not provided");
        await prisma.user.update({
          where: { id: resumeUserId },
          data: { resume_url, user_data: Prisma.DbNull },
        });
        return new Response(JSON.stringify({ success: true, message: "resume updated" }), {
          status: 200,
        });
      }

      case "upsert":
        const { id: upsertId, email: upsertEmail, name: upsertName, profile_image } = body;
        const upserted = await prisma.user.upsert({
          where: { email: upsertEmail },
          update: {
            // Always update name if provided
            ...(upsertName && { name: upsertName }),
            // Always update profile_image if provided (even for existing users)
            ...(profile_image && { profile_image: profile_image }),
          },
          create: {
            id: upsertId,
            email: upsertEmail,
            name: upsertName,
            profile_image: profile_image,
            applied_jobs: [],
          },
        });
        return new Response(JSON.stringify({ success: true, user: upserted }), { status: 200 });

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
