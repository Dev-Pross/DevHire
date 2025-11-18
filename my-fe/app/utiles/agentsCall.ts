import axios from "axios";
import getLoginUser from "./getUserData";

interface JobsData{
    "job_url":string,
    "job_description":string
}

async function sendUrl(url: string, user_id: string, password: string) {
    let progress_user: string | null
    const { data, error } = await getLoginUser();
    if(data?.user){
        progress_user = data?.user.user_metadata.email
    }
    else progress_user = null
try {
    const res = await axios.post(`http://localhost:8000/get-jobs`, {
            file_url: url,
            user_id: user_id ? user_id : "",
            password: password ? password : "",
            progress_user: progress_user ? progress_user : user_id
        });
        console.log(url)
        console.log("Server response:", res.data);
        return { data: res.data, error: null };
        
    } catch (err: any) {
    console.error("Error sending URL to server:", err);
    return { data: null, error: err };
    }
}

async function Apply_Jobs(jobs: JobsData[], url: string, user_id: string, password: string) {
     let progress_user: string | null
    const { data, error } = await getLoginUser();
    if(data?.user){
        progress_user = data?.user.user_metadata.email
    }
    else progress_user = null
    try {
    const res = await axios.post(`http://localhost:8000/apply-jobs`, {
            user_id: user_id ? user_id : "",
            password: password ? password : "",
            resume_url: url,
            jobs:jobs,
            progress_user: progress_user ? progress_user : user_id

        });
        console.log(res)
        console.log("apply server response:", res.data);
        return { data: res.data, error: null };
        
    } catch (err : any) {
    console.error("Error sending URL to apply server:", err);
    return { data: null, error: err };
    }
}


export {sendUrl, Apply_Jobs}
    