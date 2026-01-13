package fer.project.central.service;

import fer.project.central.exception.BtsNotFoundException;
import fer.project.central.exception.DuplicateBtsException;
import fer.project.central.model.BTS;
import fer.project.central.repository.BTSRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class BTSService {

    private final BTSRepository btsRepository;

    public List<BTS> getAllBTS() {
        return btsRepository.findAll();
    }

    public Optional<BTS> getBTSByBtsId(String btsId) {
        return btsRepository.findByBtsId(btsId);
    }

    public BTS registerBTS(BTS bts) {
        if (btsRepository.findByBtsId(bts.getBtsId()).isPresent()) {
            throw new DuplicateBtsException(bts.getBtsId());
        }

        bts.setCreatedAt(LocalDateTime.now());
        bts.setUpdatedAt(LocalDateTime.now());

        return btsRepository.save(bts);
    }

    public BTS updateBTSStatus(String btsId, String newStatus) {
        BTS bts = getBTSByBtsId(btsId)
                .orElseThrow(() -> new BtsNotFoundException(btsId));

        if (!bts.getStatus().equals(newStatus)) {
            bts.setStatus(newStatus);
            bts.setUpdatedAt(LocalDateTime.now());
            return btsRepository.save(bts);
        }

        return bts;
    }

}
