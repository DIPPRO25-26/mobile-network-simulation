package fer.project.central.repository;

import fer.project.central.model.BTS;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface BTSRepository extends JpaRepository<BTS, Long> {
    Optional<BTS> findByBtsId(String btsId);
}
