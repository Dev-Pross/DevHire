import axios from "axios";


async function sendUrl(url: string, user_id: string, password: string) {
try {
        const res = await axios.post("http://127.0.0.1:8000/get-jobs", {
            file_url: url,
            user_id: user_id,
            password: password
        });
        console.log(res)
        console.log("Server response:", res.data);
        return res.data
        
    } catch (err) {
    console.error("Error sending URL to server:", err);
    return err
    }
}


export default sendUrl
    