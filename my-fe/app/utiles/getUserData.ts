import { supabase } from "./supabaseClient";

export default async function getLoginUser() {
    const{ data, error} = await supabase.auth.getSession()
    if(error)
        return {data: null,error: error}
    else
        return {data: data.session, error: null}
}