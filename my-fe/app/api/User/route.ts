import prisma from "@/app/utiles/database";
import { Prisma } from "@prisma/client";


async function insert_user(data: any) {
  return prisma.user.create({ data })
}

async function update_row(id: string, data: { column: string, value: any }) {
  if (!id) {
    throw new Error("id not provided")
  }
  if (!data.column) {
    throw new Error("column name not provided")
  }
  if (data.value === undefined) {
    throw new Error("value not provided")
  }
  // A null value clears the column. Prisma rejects a bare JS null for a Json
  // column, so translate it to the DB-null token.
  const value = data.value === null ? Prisma.DbNull : data.value;
  return prisma.user.update({
    where: { id: id },
    data: {
      [data.column]: value
    }
  })
}

async function fetch(id: any) {
  if (!id) {
    throw new Error("id not provided")
  }
  let user = await prisma.user.findFirst({
    where: { id }
  });
  if (user) {
    const now = new Date();
    const lastReset = user.credits_last_reset ? new Date(user.credits_last_reset) : new Date(0);
    const lastApplyReset = (user as any).daily_apply_date ? new Date((user as any).daily_apply_date) : new Date(0);

    const updateData: any = {};

    // Reset generation/fetch credits on a new UTC day
    if (
      lastReset.getUTCFullYear() !== now.getUTCFullYear() ||
      lastReset.getUTCMonth() !== now.getUTCMonth() ||
      lastReset.getUTCDate() !== now.getUTCDate()
    ) {
      updateData.shared_generation_credits = 5;
      updateData.fetch_jobs_credits = 2;
      updateData.credits_last_reset = now;
    }

    // Reset daily apply count on a new UTC day
    if (
      lastApplyReset.getFullYear() !== now.getUTCFullYear() ||
      lastApplyReset.getMonth() !== now.getUTCMonth() ||
      lastApplyReset.getDate() !== now.getUTCDate()
    ) {
      updateData.daily_apply_count = 0;
      updateData.daily_apply_date = now;
    }

    if (Object.keys(updateData).length > 0) {
      user = await prisma.user.update({
        where: { id: user.id },
        data: updateData
      });
    }
  }

  let max_daily_applies = 40;
  try {
    const sysConfig = await prisma.systemConfig.findUnique({
      where: { key: "MAX_DAILY_APPLY_LIMIT" }
    });
    if (sysConfig && sysConfig.value) {
      max_daily_applies = parseInt(sysConfig.value, 10);
    }
  } catch (e) {
    console.error("Failed to fetch SystemConfig MAX_DAILY_APPLY_LIMIT:", e);
  }

  return user ? { ...user, max_daily_applies } : user;
}
export async function POST(request: Request) {
  const url = new URL(request.url)
  const action = url.searchParams.get("action")
  const body = await request.json();

  try {

    switch (action) {
      case "insert":
        const created = await insert_user(body)
        return new Response(JSON.stringify({ success: true, user: created }), {
          status: 201
        });

      case "update":
        const { id, data } = body
        const updated = await update_row(id, data)
        return new Response(JSON.stringify({ success: true, message: "row updated" }), {
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

      case "deduct_credit": {
        const { id: creditUserId, type: creditType } = body;
        if (!creditUserId) throw new Error("id not provided");

        const user = await prisma.user.findFirst({ where: { id: creditUserId } });
        if (!user) throw new Error("user not found");

        // PRO users have unlimited credits
        if (user.tier === "PRO") {
          return new Response(JSON.stringify({ success: true, message: "PRO user, no deduction" }), { status: 200 });
        }

        if (creditType === "generation") {
          if (user.shared_generation_credits <= 0) {
            return new Response(JSON.stringify({ success: false, message: "Out of generation credits" }), { status: 403 });
          }
          await prisma.user.update({
            where: { id: user.id },
            data: { shared_generation_credits: user.shared_generation_credits - 1 }
          });
        } else if (creditType === "fetch") {
          if (user.fetch_jobs_credits <= 0) {
            return new Response(JSON.stringify({ success: false, message: "Out of fetch jobs credits" }), { status: 403 });
          }
          await prisma.user.update({
            where: { id: user.id },
            data: { fetch_jobs_credits: user.fetch_jobs_credits - 1 }
          });
        } else {
          throw new Error("Invalid credit type");
        }

        return new Response(JSON.stringify({ success: true, message: "Credit deducted" }), { status: 200 });
      }

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

export async function GET(request: Request) {
  const url = new URL(request.url)
  const action = url.searchParams.get("id")

  try {

    const user = await fetch(action)
    return new Response(JSON.stringify({ success: true, user: user }), { status: 200 })

  } catch (err: any) {
    return new Response(JSON.stringify({ success: false, message: err.message || "Unknown error" }),
      {
        status: 500
      })
  }
}
