import { getServerSession } from "next-auth";
import { RealNavBar } from "./components/NavBar";
import { authoptions } from "./api/auth/[...nextauth]/route";
export default function Home() {
   const session = getServerSession(authoptions)
  return (
    <div>
      <RealNavBar />

    </div>
  )
}
