"use client";
import { useRef, useState } from "react";
import { Registerr } from "../api/auth/route";

export function SignUp() {
  const [data, setData] = useState({
    username: "",
    email: "",
    password: "",
    ConfirmPassword: "",
  });

  // The error occurs because you are calling Registerr immediately and assigning its Promise
  // to the onClick handler, which expects a function, not a Promise.
  // The correct way is to define a function that calls Registerr when the button is clicked.

  const handle = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    try {
      if (data.password == data.ConfirmPassword) {
        await Registerr(data.username, data.password);
        alert("welcome to " + data.username);
      } else {
        alert("passwords are not matching ");
      }
    } catch (error) {
      alert("Registration failed");
    }
  };

  return (
    <div>
      <div>
        <input
          type="text"
          placeholder="Create Your Username"
          name="username"
          autoComplete="username"
          required
          value={data.username}
          onChange={(e) => setData({ ...data, username: e.target.value })}
        />

        <input
          type="email"
          placeholder="example@gmial.com"
          name="email"
          autoComplete="Email"
          required
          value={data.email}
          onChange={(e) => setData({ ...data, email: e.target.value })}
        />
        <input
          type="password"
          placeholder="example@gmial.com"
          name="password"
          autoComplete="Email"
          required
          value={data.password}
          onChange={(e) => setData({ ...data, password: e.target.value })}
        />

        <input
          type="password"
          placeholder="example@gmial.com"
          name="confirm Password"
          autoComplete="Confirm poassword"
          required
          value={data.ConfirmPassword}
          onChange={(e) =>
            setData({ ...data, ConfirmPassword: e.target.value })
          }
        />
        <button onClick={handle}>submit</button>
      </div>
    </div>
  );
}
