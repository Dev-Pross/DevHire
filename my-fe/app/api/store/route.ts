import { NextResponse } from "next/server";
import crypto from "crypto";
import jwt from "jsonwebtoken";

export async function POST(request: Request) {
  const { username, password } = await request.json();

  // Validate input
  if (!username || !password) {
    return NextResponse.json({ message: "Empty credentials" }, { status: 400 });
  }

  // Encryption key and IV (32 and 16 bytes respectively)
  const ENC_KEY = Buffer.from(
    "qwertyuioplkjhgfdsazxcvbnm987456",
    "utf-8"
  ) // ensure 32 bytes for AES-256
  const IV = Buffer.from("741852963qwerty0", "utf-8") // ensure 16 bytes IV

  function encryptData(plaintext: string): string {
    const cipher = crypto.createCipheriv("aes-256-cbc", ENC_KEY, IV);
    let encrypted = cipher.update(plaintext, "utf8", "base64");
    encrypted += cipher.final("base64");
    return encrypted;

    
  }

  const data = JSON.stringify({ username, password });
  const encryptCredentials = encryptData(data);

  const secret = "1w3r5y7i9plkjhgfdsazxcvbnm";

  // Correctly sign the encrypted data inside an object payload
  const token = jwt.sign({ data: encryptCredentials }, secret);

  const response = NextResponse.json(
    { message: "Credentials stored successfully" },
    { status: 200 }
  );

  response.cookies.set({
    name: "li_c",
    value: token,
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 60 * 60 * 24,
    path: "/",
  });

  return response;
}
