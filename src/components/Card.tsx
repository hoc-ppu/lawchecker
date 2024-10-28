import React from "react";

interface CardProps {
  step: string;
  info: string;
  children: React.ReactNode;
}

const Card: React.FC<CardProps> = ({ step, info, children }) => {
  return (
    <div className="card my-3">
      <div className="card-header d-flex">
        <h2 className="h6 pe-2">{step}</h2>
        <p className="h6 fw-normal text-secondary">
          <small>{info}</small>
        </p>
      </div>
      <div className="d-grid gap-2 col-9 col-lg-8 col-xl-6 mx-auto my-3">
        {children}
      </div>
    </div>
  );
};

export default Card;
