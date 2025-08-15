import React from "react";

interface Job {
  job_id: string;
  title?: string;
  job_url?: string;
  job_description?: string;
  experience?: string;
  location?: string;
  key_skills?: string[];
  source?: string;
  relevance_score?: string;
}

interface JobsListProps{
    jobs: Job[];
}
const JobsList: React.FC<JobsListProps> = ({jobs}) => {
    return (
        <div className="mt-8 w-full max-w-2xl">
      <h2 className="text-2xl font-bold mb-4 text-white">Job Listings</h2>
      <ul className="space-y-6">
        {jobs.map((job) => (
          <li
            key={job.job_id}
            className="bg-white/10 p-4 rounded-lg shadow-md"
          >
            <a
              href={job.job_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xl font-semibold text-blue-400 hover:underline"
            >
              {job.title || "No Title"}
            </a>

            <p className="text-white mt-1 whitespace-pre-wrap">
              {job.job_description || "No Description"}
            </p>

            <p className="text-gray-300 mt-2">
              <strong>Experience:</strong> {job.experience || "N/A"} |{" "}
              <strong>Location:</strong> {job.location || "N/A"} |{" "}
              <strong>Skills:</strong>{" "}
              {job.key_skills?.join(", ") || "N/A"}
            </p>

            <p className="text-gray-400 text-sm mt-1">
              Source: {job.source || "Unknown"} | Relevance Score:{" "}
              {job.relevance_score || "N/A"}
            </p>
          </li>
        ))}
      </ul>
    </div>
    );
}

export default JobsList;