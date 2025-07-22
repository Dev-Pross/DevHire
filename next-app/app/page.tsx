import { authoptions } from "./api/auth/[...nextauth]/route";
import {RealNavBar} from "./components/NavBar";
import { getServerSession } from "next-auth";
export  default async function  Home() {
  const session = await getServerSession(authoptions);
  return (
    <div>
      <div>
        <RealNavBar />
      </div>
      <div className="top-0">
        {JSON.stringify(session)}
      </div>
    </div>
  );
}
