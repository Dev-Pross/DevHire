import { NextRequest, NextResponse } from "next/server";
import jwt from "jsonwebtoken";

const JWT_SECRET = process.env.JWT_SECRET || "1w3r5y7i9plkjhgfdsazxcvbnm";

export async function GET(request: NextRequest) {
  const token = request.cookies.get("li_c")?.value;

  if (!token) {
    return NextResponse.json({ error: "Missing auth token" }, { status: 401 });
  }

  try {
    const payload: any = jwt.verify(token, JWT_SECRET);

    if (!payload.data) {
      return NextResponse.json({ error: "No encrypted data found in token" }, { status: 400 });
    }

    // Return encrypted data as is, no decryption on server
    return NextResponse.json({ encryptedData: payload.data }, { status: 200 });
  } catch (err) {
    return NextResponse.json({ error: "Invalid auth token" }, { status: 401 });
  }
}
