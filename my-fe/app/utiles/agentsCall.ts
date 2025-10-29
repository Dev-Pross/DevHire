import axios from "axios";

interface JobsData{
    "job_url":string,
    "job_description":string
}

async function sendUrl(url: string, user_id: string, password: string) {
try {
        const res = await axios.post("http://127.0.0.1:8000/get-jobs", {
            file_url: url,
            user_id: user_id,
            password: password
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
try {
        const res = await axios.post("http://127.0.0.1:8000/apply-jobs", {
            user_id: user_id,
            password: password,
            resume_url: url,
            jobs:jobs
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
    