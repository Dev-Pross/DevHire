"use client"
import React, { useEffect, useState } from 'react'
import { HeroTalent } from './Landing-Page/hero-section';
import getLoginUser from '../utiles/getUserData';

const HomePage = () => {
  const [userId, setUserId] = useState<any>(null)
  useEffect(() => {
  console.log("Effect mounted, adding event listener");
  const  updateUserId = async() => {
    const { data, error } = await getLoginUser();
      if (data) {
        setUserId(data?.user.user_metadata);
      }
  };


  updateUserId();
  window.addEventListener("loginStateChanged", updateUserId);

  return () => {
    window.removeEventListener("loginStateChanged", updateUserId);
  };
}, []);


  return (
    <>
    <HeroTalent />
    </>
  )
}

export default HomePage