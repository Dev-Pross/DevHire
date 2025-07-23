import axios from  "axios"

    const API_URL  = "http://localhost:3000/api/auth"

export async function Registerr(username : string , password : string){
    return await axios.post(`${API_URL}/Register`,{
        username : username,
        password : password 
    })
   
}