import { supabase } from "./supabaseClient";

export default async function getLoginUser() {
    const{ data, error} = await supabase.auth.getSession()
    if(error)
        return null
    else
        return data.session
}