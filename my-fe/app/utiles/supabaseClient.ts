import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_PROJECT_URL as string
const supabaseAnon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY as string

if( !supabaseUrl ||  !supabaseAnon)
    throw new Error(" No env variables")

export const supabase = createClient(supabaseUrl, supabaseAnon)