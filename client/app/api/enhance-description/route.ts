import { NextResponse } from "next/server";
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({
  apiKey: process.env.NEXT_PUBLIC_GEMINI_API_KEY!,
});

export async function POST(req: Request) {
  const { text } = await req.json();

  const response = await ai.models.generateContent({
    model: "gemini-3-pro-preview",
    contents: `Rewrite the following listing description so that it is clearer, more engaging, and easy to understand.  
Keep the same meaning and intent.  
Do NOT add extra suggestions, tips, or multiple versions.  
Do NOT explain your changes.  
Do NOT include emojis.  
Return only the improved description as plain text.\n Description:${text} `,
  });

  return NextResponse.json({
    enhanced: response.text,
  });
}
