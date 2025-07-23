export async function POST(req: Request) {
    const { username, email, password } = await req.json();
    console.log(username, password);
  
    return new Response(JSON.stringify({
      message: "Signup successful",
      username,
    }), {
      status: 201,
      headers: { "Content-Type": "application/json" },
    });
  }
  
// export {handler as POST}